from gpiozero import DigitalOutputDevice, PWMOutputDevice

# BOARD pins from src/state/robot_state_machine.py
DRIVE_PINS = (18, 11, 13, 15)  # left fwd, left back, right fwd, right back
ENABLE_PINS = (32, 33)  # left, right
PWM_HZ = 100


class Side:
    def __init__(self, enable, fwd, back):
        self.enable = PWMOutputDevice(f"BOARD{enable}", frequency=PWM_HZ)
        self.fwd = DigitalOutputDevice(f"BOARD{fwd}")
        self.back = DigitalOutputDevice(f"BOARD{back}")

    def set(self, speed):
        self.fwd.value = speed > 0
        self.back.value = speed < 0
        self.enable.value = abs(speed)

    def coast(self):
        self.enable.value = 0
        self.fwd.off()
        self.back.off()

    def close(self):
        self.coast()
        for d in (self.enable, self.fwd, self.back):
            d.close()


class Motors:
    def __init__(self, drive_pins=DRIVE_PINS, enable_pins=ENABLE_PINS):
        self.left = Side(enable_pins[0], drive_pins[0], drive_pins[1])
        self.right = Side(enable_pins[1], drive_pins[2], drive_pins[3])

    def drive(self, left, right):
        self.left.set(left)
        self.right.set(right)

    def coast(self):
        self.left.coast()
        self.right.coast()

    def close(self):
        self.left.close()
        self.right.close()
