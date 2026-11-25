#!/usr/bin/env python3
"""Stand check for the motor-control layer (rover.drivetrain). WHEELS OFF THE GROUND, about 9 s.

    sudo systemctl stop rover        # the service owns the pins; stop it first
    python3 tools/stand_check_drivetrain.py --yes-wheels-clear
    python3 tools/stand_check_drivetrain.py --fake     # dry run on any machine, no hardware, instant

Needs the encoders wired (BOARD 29 left, 31 right). Runs the real Drivetrain and TickLoop:
  1. left side alone at duty 0.4 for 1.5 s, then the right: edges per second, m/s, implied top speed
  2. both sides under the speed PI at 0.4 of top speed for 3 s: each side's speed, duty and the spread
  3. an unplugged encoder is simulated: right counts are dropped; it must raise encoder_fault <= 1.5 s
Prints one PASS/FAIL line per step and exits 1 on any FAIL. Always coasts at the end.
"""
import argparse
import sys
import time

sys.path.insert(0, __file__.rsplit("/tools/", 1)[0])

from rover import drivetrain  # noqa: E402
from rover.command import DriveCommand  # noqa: E402
from rover.drivetrain import Drivetrain  # noqa: E402
from rover.loop import FakeClock, TickLoop  # noqa: E402

PERIOD = 0.02


class Plant:
    """--fake: wheels whose edge rate follows the duty (right 10% weaker)."""

    def __init__(self, motors):
        self.motors, self.carry = motors, [0.0, 0.0]

    def read(self):
        out = []
        for i, (d, gain) in enumerate(zip((self.motors.left, self.motors.right), (1.0, 0.9))):
            self.carry[i] += abs(d) * gain * drivetrain.MAX_SPEED_MPS / drivetrain.M_PER_EDGE_LEFT * PERIOD
            n = int(self.carry[i])
            self.carry[i] -= n
            out.append(n)
        return tuple(out)

    def close(self):
        pass


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--yes-wheels-clear", action="store_true")
    ap.add_argument("--fake", action="store_true")
    args = ap.parse_args(argv)
    if not (args.fake or args.yes_wheels_clear):
        print("wheels must be clear of the ground: re-run with --yes-wheels-clear (or --fake)")
        return 2
    if args.fake:
        from rover.sim import SimMotors

        clock, motors = FakeClock(), SimMotors()
        encoders, sleep = Plant(motors), lambda s: clock.advance(s)
    else:
        from rover.encoders import GpiodEncoders
        from rover.motors import Motors

        class Real:
            def now(self):
                return time.monotonic()

        clock, motors, encoders, sleep = Real(), Motors(), GpiodEncoders(), time.sleep
    events = type("E", (), {"items": [], "emit": lambda self, name, **f: self.items.append((name, f))})()
    dr = Drivetrain(events, closed_loop=True)
    loop = TickLoop(motors, clock, drivetrain=dr)
    failed = []

    def run(seconds, left, right, drop_right=False):
        """Returns (edges per side, last measured speeds, last duty, seconds to the fault or None)."""
        total, t0 = [0, 0], clock.now()
        while clock.now() - t0 < seconds:
            now = clock.now()
            edges = encoders.read()
            if drop_right:
                edges = (edges[0], 0)
            total[0] += edges[0]
            total[1] += edges[1]
            loop.edges = edges
            loop.submit(DriveCommand(left, right, "stand", now))
            loop.tick()
            if dr.fault:
                return total, dr.speed, loop.output, clock.now() - t0
            sleep(PERIOD)
        return total, dr.speed, loop.output, None

    def step(name, ok, detail):
        print(("PASS " if ok else "FAIL ") + f"{name}: {detail}")
        if not ok:
            failed.append(name)

    try:
        for side, (l, r) in (("left", (0.4, 0.0)), ("right", (0.0, 0.4))):
            dr.closed_loop, dr.fault = False, None  # open loop: raw duty
            loop.ramp.reset()
            total, _, _, _ = run(1.5, l, r)
            n = total[0 if side == "left" else 1]
            mps = n * drivetrain.M_PER_EDGE_LEFT / 1.5
            step(f"1 {side} alone at duty 0.4", n > 5, f"{n} edges, {n / 1.5:.0f}/s = {mps:.2f} m/s, top speed about {mps / 0.4:.2f} m/s"
                 " (set max_speed_mps from this)")
            run(0.3, 0.0, 0.0)
        dr.closed_loop = True
        dr.rearm()
        loop.ramp.reset()
        _, speed, duty, _ = run(3.0, 0.4, 0.4)
        want = 0.4 * drivetrain.MAX_SPEED_MPS
        spread = abs(speed[0] - speed[1])
        step("2 PI at 0.4 of top speed", spread < 0.05 and dr.fault is None,
             f"left {speed[0]:.3f} m/s duty {duty[0]:.2f}, right {speed[1]:.3f} m/s duty {duty[1]:.2f}, want {want:.3f}, spread {spread:.3f}")
        run(0.3, 0.0, 0.0)
        dr.rearm()
        loop.ramp.reset()
        _, _, _, t = run(3.0, 0.5, 0.5, drop_right=True)
        step("3 dead right encoder", t is not None and t <= 1.6 and dr.fault and dr.fault[0] == "right",
             f"fault {dr.fault} after {t if t is None else round(t, 2)} s")
    finally:
        motors.coast()
        encoders.close()
    print("ALL PASS" if not failed else f"FAILED: {', '.join(failed)}")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
