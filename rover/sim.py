import math


class Sim:
    """Differential-drive robot in a 2D room with one ping ray.

    Walls: the box x in [0, width], y in [0, height]. Heading 0 is +x.
    """

    def __init__(self, x=1.0, y=1.0, heading=0.0, width=5.0, height=5.0,
                 max_speed=0.5, track=0.15, max_range=4.0):
        self.x, self.y, self.heading = x, y, heading
        self.width, self.height = width, height
        self.max_speed, self.track, self.max_range = max_speed, track, max_range

    def step(self, left, right, dt):
        vl, vr = left * self.max_speed, right * self.max_speed
        v = (vl + vr) / 2
        self.heading += (vr - vl) / self.track * dt
        self.x = min(max(self.x + v * math.cos(self.heading) * dt, 0.0), self.width)
        self.y = min(max(self.y + v * math.sin(self.heading) * dt, 0.0), self.height)

    def ping(self):
        dx, dy = math.cos(self.heading), math.sin(self.heading)
        best = self.max_range
        for d, p, lo, hi in ((dx, self.x, 0.0, self.width), (dy, self.y, 0.0, self.height)):
            if d > 1e-9:
                best = min(best, (hi - p) / d)
            elif d < -1e-9:
                best = min(best, (lo - p) / d)
        return best
