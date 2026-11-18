"""Bench check for the hardware-PWM servo: sweep 60-130 deg, then hold 95 deg for 10 s.

On the Pi (after rewiring and the overlay, hardware/wiring.md):  python tools/probes/servo_hwpwm_check.py
Logic only, no Pi:  python tools/probes/servo_hwpwm_check.py --root DIR --fast  (DIR holds pwmchip0/)
"""
import argparse
import sys
import time

sys.path.insert(0, __file__.rsplit("/tools/", 1)[0])
from rover.servo import HwPwmServo  # noqa: E402

ap = argparse.ArgumentParser()
ap.add_argument("--root", default="/sys/class/pwm")
ap.add_argument("--fast", action="store_true")
a = ap.parse_args()
nap = (lambda s: time.sleep(s / 50)) if a.fast else time.sleep
servo = HwPwmServo(a.root)
try:
    for ang in list(range(60, 131, 5)) + list(range(130, 59, -5)):
        servo.move(ang)
        print("angle", ang)
        nap(0.15)
    servo.move(95)
    print("hold 95 for 10 s")
    nap(10)
finally:
    servo.close()
print("done")
