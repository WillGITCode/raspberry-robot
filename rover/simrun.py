"""Run the robot's real loop in the simulated room: modes, arbiter, guard, ramp, scanner.

    python -m rover.simrun                       # explore, live top-down view on http://localhost:8090/
    python -m rover.simrun --headless --minutes 5 --furniture   # as fast as possible; prints metrics
    python -m rover.simrun --room 3x3 --seed 4 --speed 4        # a small room, 4x real time

The mode runs as a bench mode (no pad). Headless runs end with one line of metrics (closest approach,
path, bumps, looks, stucks, guard stops) and exit non-zero if the robot bumped into something:
a quick regression check for any change to a mode, the guard or the scanner.
"""
import argparse
import io
import json
import math
import random
import sys
import time

from rover.drive_input import ModeRequest
from rover.events import Events
from rover.loop import FakeClock
from rover.scanner import Scanner
from rover.servo import FakeServo
from rover.sim import Sim, SimMotors, SimPing


class SimPose:
    """Stands in for odometry on the status page: the sim's true pose, room and obstacles."""

    def __init__(self, sim):
        self.sim, self.odo = sim, self

    def read(self):
        return None  # no encoders in the sim: the drivetrain runs open loop

    def tick(self, now, output):
        pass

    def pose(self):
        s = self.sim
        return {"x": round(s.x, 3), "y": round(s.y, 3), "heading_deg": round(math.degrees(s.heading), 1),
                "room": [s.width, s.height], "obstacles": s.obstacles, "bumps": s.bumps}

    def close(self):
        pass


class OneRequest:
    """A drive input that asks for one bench mode at the start, then stays quiet."""

    def __init__(self, request):
        self.request = request

    def poll(self):
        out, self.request = ([self.request] if self.request else []), None
        return out


def furniture(width, height, rnd):
    """Two or three boxes, like a chair base or a crate, kept clear of the start corner."""
    boxes = []
    for _ in range(rnd.randint(2, 3)):
        w, h = rnd.uniform(0.3, 0.6), rnd.uniform(0.3, 0.6)
        x0, y0 = rnd.uniform(1.0, width - w - 0.3), rnd.uniform(0.3, height - h - 0.3)
        boxes.append((round(x0, 2), round(y0, 2), round(x0 + w, 2), round(y0 + h, 2)))
    return boxes


def run(args):
    from rover.main import serve

    width, height = (float(v) for v in args.room.split("x"))
    rnd = random.Random(args.seed)
    sim = Sim(x=0.6, y=0.6, heading=rnd.uniform(0, math.pi / 2), width=width, height=height,
              max_speed=args.max_speed, obstacles=furniture(width, height, rnd) if args.furniture else ())
    clock, servo, motors = FakeClock(), FakeServo(), SimMotors()
    scanner = Scanner(SimPing(sim, servo, clock), servo)
    seconds = args.minutes * 60
    log = io.StringIO() if args.headless else sys.stdout
    events = Events(log, clock)
    status = None
    if not args.headless:
        from rover.status import StatusServer

        status = StatusServer(host="127.0.0.1", port=args.port)
        print(f"live view: http://127.0.0.1:{status.port}/", file=sys.stderr)
    track = {"closest": math.inf, "path": 0.0, "last": (sim.x, sim.y)}

    def sleep(_):
        sim.step(motors.left, motors.right, 0.02)
        clock.advance(0.02)
        track["closest"] = min(track["closest"], sim.clearance())
        track["path"] += math.dist(track["last"], (sim.x, sim.y))
        track["last"] = (sim.x, sim.y)
        if not args.headless:
            time.sleep(0.02 / args.speed)

    try:
        serve(motors, clock, Quiet(), events, OneRequest(ModeRequest(args.mode, seconds, "sim", 0.0)),
              ticks=int(seconds / 0.02), sleep=sleep, commit="sim", scanner=scanner, status=status,
              pose=SimPose(sim))
    finally:
        if status is not None:
            status.close()
    names = [json.loads(x) for x in log.getvalue().splitlines()] if args.headless else []
    count = lambda ev, **kv: sum(1 for e in names if e["event"] == ev and all(e.get(k) == v for k, v in kv.items()))  # noqa: E731
    metrics = {"room": args.room, "furniture": len(sim.obstacles), "minutes": args.minutes,
               "closest_m": round(track["closest"], 3), "path_m": round(track["path"], 1), "bumps": sim.bumps,
               "looks": count("explore", state="look"), "stucks": count("explore", state="back"),
               "guard_stops": count("obstacle_limit", state="stop"), "faults": count("fault")}
    print(json.dumps(metrics))
    return 1 if sim.bumps else 0


class Quiet:
    def notify(self, message):
        pass


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--mode", default="explore")
    p.add_argument("--room", default="5x4", help="width x height in metres")
    p.add_argument("--furniture", action="store_true", help="add 2-3 boxes to the room")
    p.add_argument("--seed", type=int, default=1)
    p.add_argument("--minutes", type=float, default=2.0)
    p.add_argument("--max-speed", type=float, default=0.5, help="m/s at full command (a guess until measured)")
    p.add_argument("--headless", action="store_true", help="no live view; as fast as possible; print metrics")
    p.add_argument("--speed", type=float, default=1.0, help="live view: times real time")
    p.add_argument("--port", type=int, default=8090)
    return run(p.parse_args(argv))


if __name__ == "__main__":
    sys.exit(main())
