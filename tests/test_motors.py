from rover.motors import DRIVE_PINS, ENABLE_PINS


def test_forward_sets_duty_and_direction(motors, pins):
    motors.drive(0.5, 0.5)
    assert pins(ENABLE_PINS[0]).state == 0.5
    assert pins(ENABLE_PINS[1]).state == 0.5
    assert pins(DRIVE_PINS[0]).state == 1 and pins(DRIVE_PINS[1]).state == 0
    assert pins(DRIVE_PINS[2]).state == 1 and pins(DRIVE_PINS[3]).state == 0


def test_reverse_swaps_direction(motors, pins):
    motors.drive(-1, -1)
    assert pins(DRIVE_PINS[0]).state == 0 and pins(DRIVE_PINS[1]).state == 1
