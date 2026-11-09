from rover.command import DriveCommand
from rover.motors import DRIVE_PINS, ENABLE_PINS


def test_stale_command_coasts_every_pin(loop, clock, pins):
    loop.submit(DriveCommand(1, 1, "test", clock.now()))
    loop.tick()
    assert pins(ENABLE_PINS[0]).state == 1
    clock.advance(0.31)
    loop.tick()
    for n in (*ENABLE_PINS, *DRIVE_PINS):
        assert pins(n).state == 0
    assert loop.stale


def test_fresh_command_survives(loop, clock, pins):
    loop.submit(DriveCommand(1, 1, "test", clock.now()))
    clock.advance(0.29)
    loop.tick()
    assert pins(ENABLE_PINS[0]).state == 1
