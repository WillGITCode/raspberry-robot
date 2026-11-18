import math


class Sim:
    """Differential-drive robot in a 2D room with one ping ray.

    Walls: the box x in [0, width], y in [0, height]. Heading 0 is +x. Obstacles are boxes
    (x0, y0, x1, y1) inside the room: the ping sees them, and the robot (a point) cannot enter them;
    driving into one leaves it in place and counts a bump.
    """

    def __init__(self, x=1.0, y=1.0, heading=0.0, width=5.0, height=5.0,
                 max_speed=0.5, track=0.15, max_range=4.0, obstacles=()):
        self.x, self.y, self.heading = x, y, heading
        self.width, self.height = width, height
        self.max_speed, self.track, self.max_range = max_speed, track, max_range
        self.obstacles = [tuple(o) for o in obstacles]
        self.bumps = 0

    def step(self, left, right, dt):
        if getattr(self, "stuck", False):  # wheels spin, the robot stays (a test sets this)
            return
        vl, vr = left * self.max_speed, right * self.max_speed
        v = (vl + vr) / 2
        self.heading += (vr - vl) / self.track * dt
        x = min(max(self.x + v * math.cos(self.heading) * dt, 0.0), self.width)
        y = min(max(self.y + v * math.sin(self.heading) * dt, 0.0), self.height)
        if any(x0 <= x <= x1 and y0 <= y <= y1 for x0, y0, x1, y1 in self.obstacles):
            self.bumps += 1  # blocked: the wheels turn, the robot stays
            return
        self.x, self.y = x, y

    def clearance(self):
        """Distance from the robot to the nearest wall or obstacle edge."""
        best = min(self.x, self.y, self.width - self.x, self.height - self.y)
        for x0, y0, x1, y1 in self.obstacles:
            dx = max(x0 - self.x, 0.0, self.x - x1)
            dy = max(y0 - self.y, 0.0, self.y - y1)
            best = min(best, math.hypot(dx, dy))
        return best

    def ping(self, offset=0.0):
        """Range along heading + offset (radians, left positive) to the nearest wall."""
        dx, dy = math.cos(self.heading + offset), math.sin(self.heading + offset)
        best = self.max_range
        for d, p, lo, hi in ((dx, self.x, 0.0, self.width), (dy, self.y, 0.0, self.height)):
            if d > 1e-9:
                best = min(best, (hi - p) / d)
            elif d < -1e-9:
                best = min(best, (lo - p) / d)
        for box in self.obstacles:
            hit = _ray_box(self.x, self.y, dx, dy, box)
            if hit is not None:
                best = min(best, hit)
        return best


def _ray_box(px, py, dx, dy, box):
    """Distance along the ray to the box (slab method), or None if the ray misses it."""
    x0, y0, x1, y1 = box
    t0, t1 = 0.0, float("inf")
    for p, d, lo, hi in ((px, dx, x0, x1), (py, dy, y0, y1)):
        if abs(d) < 1e-12:
            if not lo <= p <= hi:
                return None
            continue
        a, b = (lo - p) / d, (hi - p) / d
        t0, t1 = max(t0, min(a, b)), min(t1, max(a, b))
    return t0 if t0 <= t1 else None


class SimMotors:
    """Stands in for Motors: keeps the last command; the test or runner steps the Sim with it."""

    def __init__(self):
        self.left = self.right = 0.0

    def drive(self, left, right):
        self.left, self.right = left, right

    def coast(self):
        self.left = self.right = 0.0

    def close(self):
        self.coast()


class SimPing:
    """A ping that measures the Sim along the servo's angle (95 is ahead, 10 is left).

    The echo arrives after the sound's round trip. Past the sensor's range it reads about 3.2 m,
    the real sensor's longest echo (18.5 ms), which counts as a valid "far" reading."""

    def __init__(self, sim, servo, clock, ahead=95.0):
        self.sim, self.servo, self.clock, self.ahead = sim, servo, clock, ahead
        self._pending = None

    @property
    def busy(self):
        return self._pending is not None

    def trigger(self):
        if self._pending is not None:
            return False
        from rover.ping import width_to_distance

        angle = self.servo.angle if self.servo.angle is not None else self.ahead
        d = self.sim.ping(math.radians(self.ahead - angle))
        # like the real PING))): with nothing in range it holds the echo for its longest, 18.5 ms
        self._pending = (self.clock.now(), min(d, width_to_distance(18.5e-3)))
        return True

    def poll(self):
        from rover.ping import ECHO_TIMEOUT_S, Echo

        if self._pending is None:
            return None
        t, d = self._pending
        if self.clock.now() - t < (2 * d / 343.0 if d is not None else ECHO_TIMEOUT_S):
            return None
        self._pending = None
        return Echo(d, t, None if d is not None else "no_echo")

    def close(self):
        pass
