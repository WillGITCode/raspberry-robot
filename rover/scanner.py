"""Pan-and-ping scanner: owns the servo and the ping, one call per tick, never blocks.

Patterns: "ahead" holds the servo at 95 degrees and pings every AHEAD_PERIOD_S. The servo holds
actively the whole time (pulses never stop while the service runs): on the stand, at full speed, an
unpowered servo was back-driven about 90 degrees by vibration, and the guard read 3 m "clear" with
an obstacle at 26 cm. "sweep" steps
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
        self._pings, self._errors, self._flips = 0, {}, []
        self._ahead_cm = []
        self._retried = False

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
        if echo is not None and getattr(echo, "flip_us", None) is not None:
            self._flips.append(echo.flip_us)
        if echo is not None and echo.error == "missed_rise" and not self._retried:
            # the flip to input came too late for the echo's start: ping again at once, same angle
            self._pings += 1
            self._errors["missed_rise"] = self._errors.get("missed_rise", 0) + 1
            self._retried = True
            if self.ping.trigger():
                self._last_trigger = now
            return []
        self._retried = False
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
            if r.distance is not None and r.angle == AHEAD:
                self._ahead_cm.append(r.distance * 100)
            if self.pattern in STEPS:
                self._i = (self._i + 1) % len(STEPS[self.pattern])
        if self.ping.busy:
            return out  # never move the sensor during its echo
        target = self.target()
        if self.servo.angle != target:
            wait = move_time(self.servo.angle, target)
            self._ready_at = now + (max(wait, SWEEP_DWELL_S) if self.pattern in STEPS else wait)
            self.servo.move(target)
            return out
        if self._ready_at is not None and now < self._ready_at:
            return out
        if self.pattern == "ahead" and now - self._last_trigger < AHEAD_PERIOD_S:
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
        """Pings, errors and the ping's flip time (trigger end to input) since the last call, for the
        health event. A slow flip (over the sensor's 750 us hold-off) is what makes a missed_rise."""
        flips = sorted(self._flips)
        ahead = sorted(self._ahead_cm)
        stats = {"pings": self._pings, "ping_errors": self._errors,
                 "flip_us_p50": round(flips[len(flips) // 2]) if flips else None,
                 "flip_us_max": round(flips[-1]) if flips else None,
                 "ahead_cm": [round(ahead[0], 1), round(ahead[len(ahead) // 2], 1), round(ahead[-1], 1)] if ahead else None}
        self._pings, self._errors, self._flips, self._ahead_cm = 0, {}, [], []
        return stats

    def close(self):
        for part in (self.ping, self.servo):
            try:
                part.close()
            except Exception:
                pass
