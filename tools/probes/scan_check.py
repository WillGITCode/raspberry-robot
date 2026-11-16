"""Bench probe: one full sweep with the real pan servo and PING))), then back to ahead.

Run by `tools/bench scan-check` from a temporary copy of rover/ on the Pi. Moves the servo only.
"""
import time

from rover.ping import GpiodPing
from rover.scanner import SWEEP, Scanner
from rover.servo import AHEAD, LgpioServo


def main():
    s = Scanner(GpiodPing(), LgpioServo(), pattern="sweep")
    seen, t0 = [], time.monotonic()
    try:
        while time.monotonic() - t0 < 10 and len(seen) < len(SWEEP):
            seen += s.tick(time.monotonic())
            time.sleep(0.02)
        took = time.monotonic() - t0
        s.servo.move(AHEAD)
        time.sleep(0.5)
    finally:
        s.close()
    for r in seen:
        d = f"{r.distance * 100:6.1f} cm" if r.distance is not None else f"no reading ({r.error})"
        side = "left" if r.angle < AHEAD else "right" if r.angle > AHEAD else "ahead"
        print(f"{r.angle:5.0f} deg  {side:5}  {d}")
    print(f"== {len(seen)} readings over one sweep in {took:.1f} s; servo back to ahead")


if __name__ == "__main__":
    main()
