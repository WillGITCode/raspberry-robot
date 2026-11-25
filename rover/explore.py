"""Explore: cruise, and when something is close ahead, stop, sweep, turn toward the open side.

A small state machine, one command per tick, never blocking (research 05):

    cruise --(obstacle within LOOK_AT_M ahead, or LOOK_SIDE_M at 30 degrees)--> look --(sweep seen)-->
        turn toward the widest open gap --(ahead open OPEN_FOR_S)--> cruise
    cruise fans the sensor 30 degrees either side and veers away from a side closer than SIDE_M
    cruise blocked again within REBLOCK_S of a turn --> back --> look (breaks look-turn loops at
        angled surfaces that echo away and read "far")
       \\--(no valid reading)--> wait --(readings back)--> cruise; too long blind: ask for idle
    turn --(TURN_TIMEOUT_S)--> look again; MAX_TURNS failed turns in a row: stuck, ask for idle
    cruise --(ahead not closing for STUCK_S)--> back --(BACK_S)--> look: pushing on something low
                                                 that the ping cannot see

It drives as source "robot". The obstacle guard still limits every command, so explore never
relies on itself alone to stop short. Without encoders it cannot tell a stall from a stop;
odometry will add that.
"""
from rover.move import drive_command
from rover.servo import AHEAD

CRUISE_SPEED = 0.3
TURN_SPEED = 0.45  # spinning a 4WD skid-steer needs more push than driving straight
LOOK_AT_M = 0.40  # an obstacle this close ahead: stop and look around
OPEN_M = 0.70  # ahead counts as open from here
SIDE_M = 0.40  # a fan reading 30 degrees off ahead closer than this: veer away from that side
LOOK_SIDE_M = 0.25  # ... and closer than this: stop and look (a leg or a corner coming in at an angle)
REBLOCK_S = 1.0  # blocked this soon after a turn: the "open" was false; back off before looking
PROGRESS_S = 2.0  # cruising this long counts as progress: the failed-turn count starts again
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
    """+1 to turn left, -1 to turn right (10 degrees is left): toward the widest run of neighbouring
    angles that are all open (OPEN_M or more), a gap the robot fits through, rather than one "far"
    reading, which may be an angled surface that sent the echo away. Ties go to the gap with more
    room. With no open angle at all, toward the single reading with the most room. No readings: left."""
    valid = sorted((r for r in readings if r.distance is not None), key=lambda r: r.angle)
    if not valid:
        return 1
    runs, run = [], []
    for r in valid:
        if r.distance >= OPEN_M and (not run or r.angle - run[-1].angle <= 25.0):
            run.append(r)
            continue
        if run:
            runs.append(run)
        run = [r] if r.distance >= OPEN_M else []
    if run:
        runs.append(run)
    if runs:
        best = max(runs, key=lambda g: (len(g), sum(r.distance for r in g)))
        centre = sum(r.angle for r in best) / len(best)
    else:
        centre = max(valid, key=lambda r: r.distance).angle
    if centre == AHEAD:
        left = sum(r.distance for r in valid if r.angle < AHEAD)
        right = sum(r.distance for r in valid if r.angle > AHEAD)
        return 1 if left >= right else -1
    return 1 if centre < AHEAD else -1


def side_distances(readings, now):
    """The fresh valid fan readings 30 degrees left and right of ahead: (left, right), None if none."""
    left = right = None
    for r in readings:
        if r.distance is None or now - r.time > SIDE_FRESH_S:
            continue
        if r.angle == AHEAD - 30.0:
            left = r.distance
        elif r.angle == AHEAD + 30.0:
            right = r.distance
    return left, right


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
        self._after_turn = False  # this cruise began at the end of a turn

    def enter(self):
        self.state = None

    def exit(self):
        self.scan = "ahead"

    def _go(self, state, now, **why):
        self.state, self.since = state, now
        self._mark = self._open_since = None
        self._after_turn = False
        self.scan = {"look": "sweep", "cruise": "fan"}.get(state, "ahead")
        if self.events is not None:
            self.events.emit("explore", state=state, **why)

    def _stop(self, now):
        return drive_command(0.0, 0.0, "robot", now)

    def _give_up(self, now):
        """MAX_TURNS failed turns or re-blocks with no progress between: stuck; ask for idle."""
        if self.events is not None:
            self.events.emit("explore", state="stuck", turns=self.turns)
        self.request = "idle"
        return self._stop(now)

    def tick(self, inputs):
        now, sense = inputs.now, inputs.sense
        ahead = sense.ahead
        if self.state is None:
            self._go("cruise", now)
        if self.state == "cruise":
            if ahead is None:
                ahead = sense.ahead_recent  # a missed ping or two is not blindness
            if ahead is None:
                self._go("wait", now, reason="blind")
                return self._stop(now)
            if self.turns and now - self.since >= PROGRESS_S:
                self.turns = 0  # real progress since the last failed turn
            left, right = side_distances(sense.readings, now)
            near = [d for d in (left, right) if d is not None]
            close_side = bool(near) and min(near) < LOOK_SIDE_M
            both = left is not None and right is not None and max(left, right) < SIDE_M
            if ahead.distance < LOOK_AT_M or close_side or both:
                why = dict(distance=round(ahead.distance, 3), side=round(min(near), 3) if near else None)
                if self._after_turn and now - self.since < REBLOCK_S:
                    self.turns += 1
                    if self.turns >= MAX_TURNS:
                        return self._give_up(now)
                    self._go("back", now, reason="reblocked", **why)
                    return self._stop(now)
                self._go("look", now, **why)
                return self._stop(now)
            if self._stuck(ahead, now):
                self._go("back", now, reason="stuck", distance=round(ahead.distance, 3))
                return self._stop(now)
            if left is not None and left < SIDE_M:  # left front close: veer right
                return drive_command(CRUISE_SPEED * (1 + VEER) / 2, -CRUISE_SPEED * (1 - VEER) / 2, "robot", now)  # veer right
            if right is not None and right < SIDE_M:
                return drive_command(CRUISE_SPEED * (1 + VEER) / 2, CRUISE_SPEED * (1 - VEER) / 2, "robot", now)  # veer left
            return drive_command(CRUISE_SPEED, 0.0, "robot", now)
        if self.state == "back":
            if now - self.since >= BACK_S:
                self._go("look", now, reason="backed_off")
                return self._stop(now)
            return drive_command(-BACK_SPEED, 0.0, "robot", now)
        if self.state == "wait":
            if ahead is not None or sense.ahead_recent is not None:
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
                    self._go("cruise", now)
                    self._after_turn = True
                    return self._stop(now)
            else:
                self._open_since = None
            if now - self.since > TURN_TIMEOUT_S:
                self.turns += 1
                if self.turns >= MAX_TURNS:
                    return self._give_up(now)
                self._go("look", now, reason="turn_timeout")
                return self._stop(now)
            return drive_command(0.0, TURN_SPEED * self.turn_dir, "robot", now)  # left: left side back, right forward
        return self._stop(now)
