"""Pan-and-ping scanner: owns the servo and the ping, one call per tick, never blocks.

Patterns: "ahead" holds the servo at 95 degrees and pings every AHEAD_PERIOD_S. "sweep" steps
10 -> 170 -> 10 by SWEEP_STEP, waits for the move to settle (at least SWEEP_DWELL_S) and pings
once per step. Every reading keeps the angle it was taken at. The old code's comments put 10
on the left and 170 on the right.
"""
from dataclasses import dataclass

from rover.servo import AHEAD, MAX_ANGLE, MIN_ANGLE, move_time

AHEAD_PERIOD_S = 0.04  # 25 Hz: an echo takes at most about 19 ms
SWEEP_STEP = 20.0
SWEEP_DWELL_S = 0.12
RELAX_AFTER_S = 0.5  # ahead: stop the servo pulses once it has held still this long


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


class Scanner:
    def __init__(self, ping, servo, pattern="ahead"):
        self.ping, self.servo = ping, servo
        self.pattern = pattern
        self.latest = {}  # angle -> newest Reading at that angle
        self._i = 0  # sweep index
        self._ready_at = None  # the servo has settled at its target from this time
        self._last_trigger = float("-inf")
        self._trigger_angle = None
        self._relaxed = False
        self._pings, self._errors = 0, {}

    def set_pattern(self, name):
        if name not in ("ahead", "sweep"):
            raise ValueError(f"unknown scan pattern: {name}")
        if name != self.pattern:
            self.pattern, self._i = name, 0

    def target(self):
        return AHEAD if self.pattern == "ahead" else SWEEP[self._i % len(SWEEP)]

    def tick(self, now):
        """Collect a finished echo, move the servo or start a ping. Returns this tick's new readings."""
        out = []
        echo = self.ping.poll()
        if echo is not None:
            r = Reading(self._trigger_angle, echo.distance, echo.time, echo.error)
            self.latest[r.angle] = r
            out.append(r)
            self._pings += 1
            if r.error:
                self._errors[r.error] = self._errors.get(r.error, 0) + 1
            if self.pattern == "sweep":
                self._i = (self._i + 1) % len(SWEEP)
        if self.ping.busy:
            return out  # never move the sensor during its echo
        target = self.target()
        if self.servo.angle != target:
            wait = move_time(self.servo.angle, target)
            self._ready_at = now + (max(wait, SWEEP_DWELL_S) if self.pattern == "sweep" else wait)
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

    def ahead(self, now, max_age, window=20.0):
        """The freshest valid reading within +-window degrees of ahead and at most max_age old."""
        best = None
        for r in self.latest.values():
            if r.distance is None or abs(r.angle - AHEAD) > window or now - r.time > max_age:
                continue
            if best is None or r.time > best.time:
                best = r
        return best

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
