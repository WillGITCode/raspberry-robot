"""Pan servo on lgpio's tx_servo: microsecond pulses at 50 Hz.

gpiozero on lgpio rounds PWM duty to whole percent, 200 us (about 18 degrees) for a servo, so the
servo uses lgpio directly. The pulse follows the old code's formula (duty 2 + angle/18 percent at
50 Hz): 400 us + angle * 100/9 us, kept to 10-170 degrees, ahead at 95.
"""
import os
import time

CHIP = 0
GPIO = 3  # BOARD 5 today; BOARD 12 (GPIO 18) once Boss moves it (hardware/wiring.md)
MIN_ANGLE, MAX_ANGLE, AHEAD = 10.0, 170.0, 95.0
DEG_PER_S = 400.0  # about 0.15 s per 60 degrees, kept slow on purpose for the settle estimate
SETTLE_S = 0.08  # after the move: let the horn and the sensor stop shaking


def clamp(angle):
    return max(MIN_ANGLE, min(MAX_ANGLE, angle))


def pulse_us(angle):
    return round(400 + clamp(angle) * 100 / 9)


def move_time(from_angle, to_angle):
    """Seconds until a move has finished and settled (an estimate, no feedback)."""
    if from_angle is None:
        return (MAX_ANGLE - MIN_ANGLE) / DEG_PER_S + SETTLE_S
    return abs(clamp(to_angle) - clamp(from_angle)) / DEG_PER_S + SETTLE_S


class LgpioServo:
    def __init__(self, chip=CHIP, gpio=GPIO):
        import lgpio

        self.lg, self.gpio = lgpio, gpio
        self.h = lgpio.gpiochip_open(chip)
        lgpio.gpio_claim_output(self.h, gpio, 0)
        self.angle = None

    def move(self, angle):
        self.angle = clamp(angle)
        self.lg.tx_servo(self.h, self.gpio, pulse_us(self.angle), 50)

    def relax(self):
        """Stop the pulses: the servo holds by friction and stops fidgeting."""
        self.lg.tx_servo(self.h, self.gpio, 0)

    def close(self):
        try:
            self.relax()
            time.sleep(0.03)
            self.lg.gpio_free(self.h, self.gpio)
        finally:
            self.lg.gpiochip_close(self.h)


class HwPwmServo:
    """Pan servo on the kernel hardware PWM (sysfs), 50 Hz, pulse in ns; holds actively like LgpioServo.

    Needs dtoverlay=pwm,pin=18,func=2 and the signal wire on BOARD 12 (hardware/wiring.md).
    `root` is the sysfs class dir, a fake dir in checks.
    """

    PERIOD_NS = 20_000_000

    def __init__(self, root="/sys/class/pwm", chip=0, channel=0):
        self.chip = os.path.join(root, f"pwmchip{chip}")
        if not os.path.isdir(self.chip):
            raise RuntimeError(f"{self.chip} missing: add dtoverlay=pwm,pin=18,func=2 and reboot")
        self.pwm = os.path.join(self.chip, f"pwm{channel}")
        if not os.path.isdir(self.pwm):
            self._write(os.path.join(self.chip, "export"), channel)
        self._write(os.path.join(self.pwm, "period"), self.PERIOD_NS)
        self.angle = None

    @staticmethod
    def _write(path, value):
        with open(path, "w") as f:
            f.write(str(value))

    def move(self, angle):
        self.angle = clamp(angle)
        self._write(os.path.join(self.pwm, "duty_cycle"), pulse_us(self.angle) * 1000)
        self._write(os.path.join(self.pwm, "enable"), 1)

    def relax(self):
        self._write(os.path.join(self.pwm, "enable"), 0)

    def close(self):
        self.relax()


def make_servo():
    """The servo backend: ROVER_SERVO=hwpwm for hardware PWM (BOARD 12), else lgpio on BOARD 5."""
    if os.environ.get("ROVER_SERVO") == "hwpwm":
        return HwPwmServo()
    return LgpioServo()


class FakeServo:
    def __init__(self):
        self.angle = None
        self.moves = []
        self.relaxed = True

    def move(self, angle):
        self.angle = clamp(angle)
        self.moves.append(self.angle)
        self.relaxed = False

    def relax(self):
        self.relaxed = True

    def close(self):
        self.relax()
