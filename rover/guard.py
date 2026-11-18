"""Obstacle guard: limits forward speed by the distance ahead. Reverse and turning stay free.

The drive command is split into forward speed v = (left + right) / 2 and turn w = (right - left) / 2.
Only v is limited: 0 at STOP_M or less, rising linearly to full at SLOW_M (a limit under MIN_MOVE
counts as 0). So at a wall the robot
can still back off or spin away. With no fresh valid reading ahead, forward speed is capped at
BLIND_CAP (no boost), and a close reading from the last MEMORY_S still counts: a failed ping is
never read as "clear".
"""

STOP_M = 0.20
SLOW_M = 0.60
MIN_MOVE = 0.1  # a limit below this snaps to zero: the motors don't turn that slowly anyway, and it
                # ends the creep toward STOP_M (the stop lands at about 24 cm)
FRESH_S = 0.5
MEMORY_S = 2.0
BLIND_CAP = 0.3
EVENT_HOLD_S = 0.15  # a new state is logged once it has held this long; "stop" is logged at once


def speed_limit(distance):
    """The highest forward speed allowed with an obstacle at `distance` metres."""
    v = max(0.0, min(1.0, (distance - STOP_M) / (SLOW_M - STOP_M)))
    return v if v >= MIN_MOVE else 0.0


class ObstacleGuard:
    def __init__(self, scanner=None, events=None):
        self.scanner, self.events = scanner, events
        self.state = None  # clear, slow, stop or blind: applied every tick
        self.limit_value = BLIND_CAP
        self.distance = None
        self._last_valid = None
        self._since = None  # when the current state began
        self._logged = None  # the last state written to the log

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
            self.state, self._since = state, now
        if state != self._logged and (state == "stop" or now - self._since >= EVENT_HOLD_S):
            self._logged = state
            if self.events is not None:
                self.events.emit("obstacle_limit", state=state, distance=self.distance, limit=vmax)
        v, w = (left + right) / 2, (right - left) / 2
        if v <= vmax:
            return left, right
        return vmax - w, vmax + w
