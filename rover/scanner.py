"""Pan-and-ping scanner: owns the servo and the ping, one call per tick, never blocks.

Patterns: "ahead" holds the servo at 95 degrees and pings every AHEAD_PERIOD_S. "sweep" steps
10 -> 170 -> 10 by SWEEP_STEP, waits for the move to settle (at least SWEEP_DWELL_S) and pings
once per step. "fan" steps ahead, 30 left, ahead, 30 right (about 0.7 s a round): it catches walls
met at a shallow angle, which never echo straight back, and still reads ahead every other ping. Every reading keeps the angle it was taken at. The old code's comments put 10
on the left and 170 on the right.
"""
from collections import deque
from dataclasses import dataclass

from rover.servo import AHEAD, MAX_ANGLE, MIN_ANGLE, move_time

AHEAD_PERIOD_S = 0.04  # 25 Hz: an echo takes at most about 19 ms
SWEEP_STEP = 20.0
SWEEP_DWELL_S = 0.12
RELAX_AFTER_S = 0.5  # ahead: stop the servo pulses once it has held still this long
NEAR_S = 0.2  # ahead() takes the nearest valid echo of the last NEAR_S: a closer echo wins at once
HISTORY_S = 1.0  # valid readings kept for ahead()


@dataclass(frozen=True)
class Reading:
    angle: float
    distance: float | None  # metres, None when there is no reading
    time: float
    error: str | None = None


def sweep_angles(step=SWEEP_STEP):
    up, a = [], MIN_ANGLE
    while a < MAX_ANGLE:
        up.append(a)
        a += step
    up.append(MAX_ANGLE)
    return up + up[-2:0:-1]  # 10 .. 170 .. 30, then round again from 10


SWEEP = sweep_angles()
FAN = [AHEAD, AHEAD - 30.0, AHEAD, AHEAD + 30.0]
STEPS = {"sweep": SWEEP, "fan": FAN}


class Scanner:
    def __init__(self, ping, servo, pattern="ahead"):
        self.ping, self.servo = ping, servo
        self.pattern = pattern
        self.latest = {}  # angle -> newest Reading at that angle, valid or not (the radar)
        self.history = deque()  # valid readings of the last HISTORY_S (the guard)
        self._i = 0  # sweep index
        self._ready_at = None  # the servo has settled at its target from this time
        self._last_trigger = float("-inf")
        self._trigger_angle = None
        self._relaxed = False
        self._pings, self._errors = 0, {}

    def set_pattern(self, name):
        if name not in ("ahead", "sweep", "fan"):
            raise ValueError(f"unknown scan pattern: {name}")
        if name != self.pattern:
            self.pattern, self._i = name, 0

    def target(self):
        if self.pattern == "ahead":
            return AHEAD
        steps = STEPS[self.pattern]
        return steps[self._i % len(steps)]

    def tick(self, now):
        """Collect a finished echo, move the servo or start a ping. Returns this tick's new readings."""
        out = []
        echo = self.ping.poll()
        if echo is not None:
            r = Reading(self._trigger_angle, echo.distance, echo.time, echo.error)
            self.latest[r.angle] = r
            if r.distance is not None:
                self.history.append(r)
            while self.history and now - self.history[0].time > HISTORY_S:
                self.history.popleft()
            out.append(r)
            self._pings += 1
            if r.error:
                self._errors[r.error] = self._errors.get(r.error, 0) + 1
            if self.pattern in STEPS:
                self._i = (self._i + 1) % len(STEPS[self.pattern])
        if self.ping.busy:
            return out  # never move the sensor during its echo
        target = self.target()
        if self.servo.angle != target:
            wait = move_time(self.servo.angle, target)
            self._ready_at = now + (max(wait, SWEEP_DWELL_S) if self.pattern in STEPS else wait)
            self.servo.move(target)
            self._relaxed = False
            return out
        if self._ready_at is not None and now < self._ready_at:
            return out
        if self.pattern == "ahead":
            if not self._relaxed and self._ready_at is not None and now - self._ready_at >= RELAX_AFTER_S:
                self.servo.relax()
                self._relaxed = True
            if now - self._last_trigger < AHEAD_PERIOD_S:
                return out
        if self.ping.trigger():
            self._last_trigger, self._trigger_angle = now, target
        return out

    def ahead(self, now, max_age, window=20.0, near_s=NEAR_S):
        """The nearest valid reading within +-window degrees of ahead: over the last near_s if there
        are any, else over the last max_age. None if there is no valid reading that fresh.

        Nearest, not newest: the ping's wide cone often sees two surfaces, and a closer one must win.
        A failed ping never hides the valid readings just before it."""
        found = [r for r in self.history
                 if abs(r.angle - AHEAD) <= window and 0.0 <= now - r.time <= max_age]
        if not found:
            return None
        recent = [r for r in found if now - r.time <= near_s] or found
        return min(recent, key=lambda r: r.distance)

    def take_stats(self):
        """Pings and errors since the last call (for the health event)."""
        stats = {"pings": self._pings, "ping_errors": self._errors}
        self._pings, self._errors = 0, {}
        return stats

    def close(self):
        for part in (self.ping, self.servo):
            try:
                part.close()
            except Exception:
                pass
