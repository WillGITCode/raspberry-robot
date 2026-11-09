from rover.motors import DRIVE_PINS, ENABLE_PINS
from rover.stop import stop


def test_stop_leaves_every_pin_low(motors, pins):
    motors.drive(1.0, -1.0)
    assert pins(32).state > 0
    stop(motors)
    for n in DRIVE_PINS + ENABLE_PINS:
        assert pins(n).state == 0
