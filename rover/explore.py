"""Explore: cruise, and when something is close ahead, stop, sweep, turn toward the open side.

A small state machine, one command per tick, never blocking (research 05):

    cruise --(obstacle within LOOK_AT_M)--> look --(sweep seen)--> turn --(ahead open)--> cruise
    cruise fans the sensor 30 degrees either side and veers away from a side closer than SIDE_M
       \\--(no valid reading)--> wait --(readings back)--> cruise; too long blind: ask for idle
    turn --(TURN_TIMEOUT_S)--> look again; MAX_TURNS failed turns in a row: stuck, ask for idle
    cruise --(ahead not closing for STUCK_S)--> back --(BACK_S)--> look: pushing on something low
                                                 that the ping cannot see

It drives as source "robot". The obstacle guard still limits every command, so explore never
relies on itself alone to stop short. Without encoders it cannot tell a stall from a stop;
odometry will add that.
"""
from rover.command import DriveCommand
from rover.servo import AHEAD

CRUISE_SPEED = 0.3
TURN_SPEED = 0.45  # spinning a 4WD skid-steer needs more push than driving straight
LOOK_AT_M = 0.40  # an obstacle this close ahead: stop and look around
OPEN_M = 0.70  # ahead counts as open from here
SIDE_M = 0.40  # a fan reading 30 degrees off ahead closer than this: veer away from that side
VEER = 0.5  # the inner side's share of the cruise speed while veering
SIDE_FRESH_S = 1.0
SETTLE_S = 0.3  # readings older than this, after a state change, are ignored for the decision
OPEN_FOR_S = 0.3  # the turn ends once ahead has stayed open this long (an obstacle may come and go)
LOOK_TIMEOUT_S = 3.5  # a full 10-170 pass takes about 1.5 s
TURN_TIMEOUT_S = 4.0
MAX_TURNS = 3
BLIND_WAIT_S = 5.0
STUCK_S = 3.0  # cruising this long while the obstacle ahead gets no closer: stuck
STUCK_CHANGE_M = 0.05  # ... "no closer" means the reading moved by less than this, either way
STUCK_RANGE_M = 2.5  # beyond this the reading may just be the sensor's limit: never "stuck"
BACK_S = 0.8
BACK_SPEED = 0.3
SWEEP_ANGLES = 9  # 10, 30, ..., 170


def choose_side(readings):
    """+1 to turn left, -1 to turn right: toward the angle with the most room (10 is left).
    No readings: left."""
    valid = [r for r in readings if r.distance is not None]
    if not valid:
        return 1
    best = max(valid, key=lambda r: r.distance)
    if best.angle == AHEAD:
        left = sum(r.distance for r in valid if r.angle < AHEAD)
        right = sum(r.distance for r in valid if r.angle > AHEAD)
        return 1 if left >= right else -1
    return 1 if best.angle < AHEAD else -1


def side_close(readings, now):
    """+1 if the left front is close, -1 if the right front is, 0 if neither (or both: look)."""
    left = right = False
    for r in readings:
        if r.distance is None or now - r.time > SIDE_FRESH_S or r.distance >= SIDE_M:
            continue
        if r.angle == AHEAD - 30.0:
            left = True
        elif r.angle == AHEAD + 30.0:
            right = True
    return 1 if left and not right else -1 if right and not left else (2 if left else 0)


class ExploreMode:
    scan = "ahead"

    def _stuck(self, ahead, now):
        """Cruising, yet the obstacle ahead gets no closer for STUCK_S: the wheels are not moving
        the robot (something low the ping misses, or a stall)."""
        if ahead.distance >= STUCK_RANGE_M:
            self._mark = None
            return False
        if self._mark is None or abs(ahead.distance - self._mark[1]) > STUCK_CHANGE_M:
            self._mark = (now, ahead.distance)  # the robot is moving: restart the window
            return False
        return now - self._mark[0] >= STUCK_S

    def __init__(self):
        self.state, self.since = None, None
        self.turn_dir, self.turns = 1, 0
        self.request = None  # set to "idle" to ask the manager to leave this mode
        self.events = None  # given by the mode manager
        self._mark = None  # (time, distance) where the stuck check started
        self._open_since = None

    def enter(self):
        self.state = None

    def exit(self):
        self.scan = "ahead"

    def _go(self, state, now, **why):
        self.state, self.since = state, now
        self._mark = self._open_since = None
        self.scan = {"look": "sweep", "cruise": "fan"}.get(state, "ahead")
        if self.events is not None:
            self.events.emit("explore", state=state, **why)

    def _stop(self, now):
        return DriveCommand(0.0, 0.0, "robot", now)

    def tick(self, inputs):
        now, sense = inputs.now, inputs.sense
        ahead = sense.ahead
        if self.state is None:
            self._go("cruise", now)
        if self.state == "cruise":
            if ahead is None:
                self._go("wait", now, reason="blind")
                return self._stop(now)
            side = side_close(sense.readings, now)
            if ahead.distance < LOOK_AT_M or side == 2:
                self._go("look", now, distance=round(ahead.distance, 3), sides_close=side == 2)
                return self._stop(now)
            if self._stuck(ahead, now):
                self._go("back", now, reason="stuck", distance=round(ahead.distance, 3))
                return self._stop(now)
            if side == 1:  # left front close: veer right
                return DriveCommand(CRUISE_SPEED, CRUISE_SPEED * VEER, "robot", now)
            if side == -1:
                return DriveCommand(CRUISE_SPEED * VEER, CRUISE_SPEED, "robot", now)
            return DriveCommand(CRUISE_SPEED, CRUISE_SPEED, "robot", now)
        if self.state == "back":
            if now - self.since >= BACK_S:
                self._go("look", now, reason="backed_off")
                return self._stop(now)
            return DriveCommand(-BACK_SPEED, -BACK_SPEED, "robot", now)
        if self.state == "wait":
            if ahead is not None:
                self._go("cruise", now)
            elif now - self.since > BLIND_WAIT_S:
                self.request = "idle"
            return self._stop(now)
        if self.state == "look":
            seen = {r.angle: r for r in sense.readings if r.time >= self.since}
            if len(seen) >= SWEEP_ANGLES or now - self.since > LOOK_TIMEOUT_S:
                self.turn_dir = choose_side(seen.values())
                self._go("turn", now, direction="left" if self.turn_dir > 0 else "right")
            return self._stop(now)
        if self.state == "turn":
            fresh = ahead is not None and ahead.time >= self.since + SETTLE_S
            if fresh and ahead.distance >= OPEN_M:
                if self._open_since is None:
                    self._open_since = now
                if now - self._open_since >= OPEN_FOR_S:
                    self.turns = 0
                    self._go("cruise", now)
                    return self._stop(now)
            else:
                self._open_since = None
            if now - self.since > TURN_TIMEOUT_S:
                self.turns += 1
                if self.turns >= MAX_TURNS:
                    if self.events is not None:
                        self.events.emit("explore", state="stuck", turns=self.turns)
                    self.request = "idle"
                else:
                    self._go("look", now, reason="turn_timeout")
                return self._stop(now)
            s = TURN_SPEED * self.turn_dir
            return DriveCommand(-s, s, "robot", now)  # left: left side back, right side forward
        return self._stop(now)
