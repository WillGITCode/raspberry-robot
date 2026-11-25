"""One drive API: drive(speed, turn), distance(m), turn(deg). Every move has a time cap and a distance cap.

`mix(speed, turn)` is the pure part: a forward speed and a turn (positive = counter-clockwise, left)
become per-side target speeds, scaled down together if one would pass 1. Modes (explore) use it for
their per-tick commands. `Mover` runs a move to its end against the odometry:

    mover = Mover(); mover.distance(0.5)       # or .turn(90), or .drive(0.3, 0.1, seconds=2)
    cmd = mover.tick(now, odo)                  # a DriveCommand each tick; None once done
    mover.done, mover.reason                    # reason: distance, angle, time, distance_cap

The commands are target speeds like any other: the deadman, guard, ramp and the encoder stop still
come first (rover.loop). turn() reads the heading, so it needs the gyro (or a track in the odometry);
without a heading it ends at its time cap with reason "time".
"""
import math

from rover.command import DriveCommand

MAX_S = 10.0  # default time cap of a move
MAX_M = 3.0  # default path length cap
SPEED = 0.3  # distance(): default speed
TURN_RATE = 0.45  # turn(): default spin speed (a 4WD skid-steer needs more push than driving straight)
TURN_TOLERANCE_DEG = 2.0


def mix(speed, turn):
    """(left, right) target speeds for a forward speed and a turn, both -1..1; turn > 0 is counter-clockwise."""
    left, right = speed - turn, speed + turn
    scale = max(1.0, abs(left), abs(right))
    return left / scale, right / scale


def drive_command(speed, turn, source, now):
    left, right = mix(speed, turn)
    return DriveCommand(left, right, source, now)


def _wrap(a):
    return math.atan2(math.sin(a), math.cos(a))


class Mover:
    def __init__(self, source="bench"):
        self.source = source
        self.done, self.reason = True, None
        self._plan = None

    def _start(self, speed, turn, max_s, max_m, goal):
        for v in (speed, turn):
            if not -1.0 <= v <= 1.0:
                raise ValueError(f"speed out of range: {v}")
        max_s = MAX_S if max_s is None else min(max_s, MAX_S)
        max_m = MAX_M if max_m is None else min(max_m, MAX_M)
        if max_s <= 0 or max_m <= 0:
            raise ValueError("a move needs a positive time cap and distance cap")
        self._plan = {"speed": speed, "turn": turn, "max_s": max_s, "max_m": max_m, "goal": goal, "start": None}
        self.done, self.reason = False, None
        return self

    def drive(self, speed, turn=0.0, seconds=None, metres=None):
        """Drive until the time or distance cap, whichever first (the defaults are the settings' caps)."""
        return self._start(speed, turn, seconds, metres, ("caps", 0.0))

    def distance(self, metres, speed=None, seconds=None):
        """Drive `metres` straight (negative: backward), then stop. More than the distance cap is an error."""
        if abs(metres) > MAX_M:
            raise ValueError(f"{metres} m is past the {MAX_M:g} m cap")
        speed = abs(SPEED if speed is None else speed) * (1.0 if metres >= 0 else -1.0)
        return self._start(speed, 0.0, seconds, abs(metres) + 0.05, ("distance", abs(metres)))

    def turn(self, degrees, rate=None, seconds=None):
        """Spin in place by `degrees` (positive: counter-clockwise, left), then stop."""
        rate = abs(TURN_RATE if rate is None else rate) * (1.0 if degrees >= 0 else -1.0)
        return self._start(0.0, rate, seconds, None, ("angle", math.radians(degrees)))

    def stop(self, reason="stopped"):
        self.done, self.reason = True, reason

    def tick(self, now, odo):
        """The command for this tick, or None once the move is done (see .reason)."""
        if self.done:
            return None
        p = self._plan
        if p["start"] is None:
            p["start"] = {"t": now, "path": odo.distance, "x": odo.x, "y": odo.y, "heading": odo.heading, "turned": 0.0}
        s = p["start"]
        turned = s["turned"] + _wrap(odo.heading - s["heading"])
        s["turned"], s["heading"] = turned, odo.heading
        path = odo.distance - s["path"]
        kind, goal = p["goal"]
        if kind == "distance" and math.hypot(odo.x - s["x"], odo.y - s["y"]) >= goal - 0.005:
            return self._end("distance")
        if kind == "angle" and abs(turned) >= abs(goal) - math.radians(TURN_TOLERANCE_DEG):
            return self._end("angle")
        if path >= p["max_m"]:
            return self._end("distance_cap")
        if now - s["t"] >= p["max_s"]:
            return self._end("time")
        return drive_command(p["speed"], p["turn"], self.source, now)

    def _end(self, reason):
        self.done, self.reason = True, reason
        return None
