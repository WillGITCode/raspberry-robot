"""Obstacle guard: limits forward speed by the distance ahead. Reverse and turning stay free.

The drive command is split into forward speed v = (left + right) / 2 and turn w = (right - left) / 2.
Only v is limited: 0 at STOP_M or less, rising linearly to full at SLOW_M. So at a wall the robot
can still back off or spin away. With no fresh valid reading ahead, forward speed is capped at
BLIND_CAP (no boost), and a close reading from the last MEMORY_S still counts: a failed ping is
never read as "clear".
"""

STOP_M = 0.20
SLOW_M = 0.60
FRESH_S = 0.5
MEMORY_S = 2.0
BLIND_CAP = 0.3


def speed_limit(distance):
    """The highest forward speed allowed with an obstacle at `distance` metres."""
    return max(0.0, min(1.0, (distance - STOP_M) / (SLOW_M - STOP_M)))


class ObstacleGuard:
    def __init__(self, scanner=None, events=None):
        self.scanner, self.events = scanner, events
        self.state = None  # clear, slow, stop or blind
        self.limit_value = BLIND_CAP
        self.distance = None
        self._last_valid = None

    def limit(self, left, right, now):
        r = self.scanner.ahead(now, FRESH_S) if self.scanner is not None else None
        if r is not None:
            self._last_valid = r
            self.distance = r.distance
            vmax = speed_limit(r.distance)
            state = "clear" if vmax >= 1.0 else "stop" if vmax <= 0.0 else "slow"
        else:
            self.distance = None
            vmax = BLIND_CAP
            lv = self._last_valid
            if lv is not None and now - lv.time <= MEMORY_S:
                vmax = min(vmax, speed_limit(lv.distance))
            state = "blind"
        self.limit_value = vmax
        if state != self.state:
            self.state = state
            if self.events is not None:
                self.events.emit("obstacle_limit", state=state, distance=self.distance, limit=vmax)
        v, w = (left + right) / 2, (right - left) / 2
        if v <= vmax:
            return left, right
        return vmax - w, vmax + w
