"""Speed control for the two sides: target speed in, motor duty out. One deep module, three parts.

The robot's commands (pad, explore, bench, moves) are target speeds as a fraction of the top speed,
-1..1 per side. The loop filters them (deadman, guard, ramp); this layer then turns each side's
target into a duty:

    encoders present:  duty = feed-forward (target / top speed) + a PI correction from the side's
                       measured speed (edges per second x metres per edge), clamped
    no encoders:       duty = target, with the left/right trim (open loop)

It also watches the encoders. A side driven hard that makes no edges for a window, or one that makes
impossible edge rates (motor noise flooding the input), is a fault: `encoder_fault` event, the motors
coast, and the stop stays latched (the pad's Start re-arms it, see rover.robot) until the cause is fixed.

Settings (rover.settings) set every constant here; each is read when used. The spike filter lives with
the encoders (rover.encoders.SpikeFilter), because it works on edge timestamps.
"""
from collections import deque

M_PER_EDGE_LEFT = 0.0103  # metres per edge, measured on the floor (bench, 2026-11); the sides differ a little
M_PER_EDGE_RIGHT = 0.0103
TRIM = 0.0  # open loop only: right duty x (1 + trim), left x (1 - trim). The bench drift (8-10 cm right per m at 0.5) is about +0.025; the sim assumes straight motors, so 0 until set on the robot
MAX_SPEED_MPS = 0.8  # speed at duty 1.0 (a first guess: tools/stand_check_drivetrain.py measures it)
KP = 0.6  # duty per m/s of speed error
KI = 1.5  # duty per m of position error
MAX_CORRECTION = 0.3  # the PI never adds or removes more duty than this
DUTY_MAX = 0.85  # the PI never drives a side above this (at 1.0 motor noise blinds the ping), unless it was commanded
FAULT_DUTY = 0.35  # a side driven at least this hard ...
FAULT_WINDOW_S = 1.0  # ... with no edge for this long is an encoder fault
MAX_EDGE_HZ = 150.0  # more edges per second than this on a side is noise, not a wheel (full speed is about 100)
RATE_WINDOW_S = 0.3  # speed is measured over this long: at 20 ms ticks a slow wheel makes 0 or 1 edge a tick
MAX_DT = 0.1


class Wheel:
    """One side: its speed measurement, PI state and fault watch."""

    def __init__(self, name):
        self.name = name
        self.reset()
        self.samples = deque()
        self.t0 = None

    def reset(self):
        self.integral = 0.0
        self.quiet_s = 0.0  # time driven hard with no edge

    def measure(self, now, edges):
        """Edges per second over the last RATE_WINDOW_S."""
        if self.t0 is None:
            self.t0 = now
        self.samples.append((now, edges))
        while self.samples and self.samples[0][0] <= now - RATE_WINDOW_S:
            self.samples.popleft()
        span = min(RATE_WINDOW_S, now - self.t0)
        self.rate_hz = sum(n for _, n in self.samples) / span if span > 0 else 0.0
        self.span = span
        return self.rate_hz

    def fault_check(self, commanded, edges, dt):
        """The reason this side's encoder looks broken, or None."""
        if self.span >= RATE_WINDOW_S / 2 and self.rate_hz > MAX_EDGE_HZ:
            return "edge_rate"
        if abs(commanded) >= FAULT_DUTY and edges == 0:
            self.quiet_s += dt
            if self.quiet_s >= FAULT_WINDOW_S:
                return "no_edges"
        else:
            self.quiet_s = 0.0
        return None


class Drivetrain:
    def __init__(self, events=None, closed_loop=False):
        self.events = events
        self.closed_loop = closed_loop  # true when there are encoders to read
        self.wheels = (Wheel("left"), Wheel("right"))
        self.fault = None  # (side, reason) while latched
        self.speed = (0.0, 0.0)  # measured m/s per side, unsigned
        self._t = None

    def reset(self):
        """Coasting: the PI starts again from nothing."""
        for w in self.wheels:
            w.reset()
        self._t = None

    def rearm(self):
        if self.fault is not None and self.events is not None:
            self.events.emit("encoder_rearm")
        self.fault = None
        for w in self.wheels:
            w.reset()
            w.samples.clear()
            w.t0 = None

    def duty(self, now, targets, edges=None):
        """Motor duty (left, right) for these target speeds. edges: (left, right) counts since the
        last call, or None with no encoders. While faulted: (0, 0)."""
        dt = 0.0 if self._t is None else min(max(now - self._t, 0.0), MAX_DT)
        self._t = now
        if self.fault is not None:
            return 0.0, 0.0
        if not (self.closed_loop and edges is not None):
            return self._open_loop(targets)
        m_per_edge = (M_PER_EDGE_LEFT, M_PER_EDGE_RIGHT)
        out, speeds = [], []
        for i, (wheel, target) in enumerate(zip(self.wheels, targets)):
            wheel.measure(now, edges[i])
            speed = wheel.rate_hz * m_per_edge[i]
            speeds.append(speed)
            duty = self._pi(wheel, target, speed, dt)
            reason = wheel.fault_check(target, edges[i], dt)  # the commanded level, not the PI's own push
            if reason:
                self._latch(wheel.name, reason, duty, wheel.rate_hz)
                return 0.0, 0.0
            out.append(duty)
        self.speed = tuple(speeds)
        return tuple(out)

    def _open_loop(self, targets):
        left, right = targets
        return _clamp(left * (1.0 - TRIM)), _clamp(right * (1.0 + TRIM))

    def _pi(self, wheel, target, speed, dt):
        if target == 0:
            wheel.reset()
            return 0.0
        sign = 1.0 if target > 0 else -1.0
        want = abs(target) * MAX_SPEED_MPS
        ff = abs(target)
        err = want - speed
        limit = MAX_CORRECTION / KI if KI else 0.0
        wheel.integral = min(max(wheel.integral + err * dt, -limit), limit)
        corr = min(max(KP * err + KI * wheel.integral, -MAX_CORRECTION), MAX_CORRECTION)
        duty = min(max(ff + corr, 0.0), max(DUTY_MAX, abs(target)))
        return sign * duty

    def _latch(self, side, reason, duty, rate_hz):
        self.fault = (side, reason)
        if self.events is not None:
            self.events.emit("encoder_fault", side=side, reason=reason, duty=round(duty, 3),
                             edges_per_s=round(rate_hz, 1))
            self.events.emit("fault", error=f"encoder fault ({side}: {reason}); stopped until re-armed")


def _clamp(v):
    return min(max(v, -1.0), 1.0)
