ACCEL_PER_S = 4.0  # 0 to full speed in 0.25 s
PERIOD_S = 0.02  # the step used on the first tick after a coast


class Ramp:
    """Limits how fast each side speeds up. Slowing, stopping and coasting are immediate,
    and a change of direction goes through zero first. Soft starts cut current spikes."""

    def __init__(self, accel_per_s=ACCEL_PER_S, period=PERIOD_S):
        self.accel, self.period = accel_per_s, period
        self.reset()

    def reset(self):
        self.left = self.right = 0.0
        self.t = None

    def apply(self, left, right, now):
        dt = self.period if self.t is None else min(max(now - self.t, 0.0), 2 * self.period)
        self.t = now
        step = self.accel * dt
        self.left = _limit(self.left, left, step)
        self.right = _limit(self.right, right, step)
        return self.left, self.right


def _limit(cur, target, step):
    if cur * target <= 0:  # stopping, starting or reversing: from zero
        cur = 0.0
    if abs(target) <= abs(cur):
        return target
    return (1.0 if target > 0 else -1.0) * min(abs(target), abs(cur) + step)
