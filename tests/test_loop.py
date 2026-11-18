import time

import pytest

from rover.command import DriveCommand


def test_sleep_inside_tick_raises(loop, clock, no_sleep):
    loop.submit(DriveCommand(0.2, 0.2, "test", clock.now()))
    loop.tick()  # logic never sleeps
    with pytest.raises(AssertionError):
        time.sleep(0)


def test_no_command_coasts(loop):
    loop.tick()
    assert loop.stale


def test_ramp_takes_13_ticks_to_full_and_stops_at_once(loop, clock, motors):
    ticks = 0
    while loop.output[0] < 1.0:
        loop.submit(DriveCommand(1.0, 1.0, "test", clock.now()))
        loop.tick()
        clock.advance(0.02)
        ticks += 1
        assert ticks < 50
    assert ticks == 13  # 4.0 per second at 50 Hz is 0.08 per tick
    loop.submit(DriveCommand(0.0, 0.0, "test", clock.now()))
    loop.tick()
    assert loop.output == (0.0, 0.0) and motors.left.enable.value == 0


def test_ramp_slows_at_once_and_reverses_through_zero(loop, clock):
    for _ in range(20):
        loop.submit(DriveCommand(0.8, 0.8, "test", clock.now()))
        loop.tick()
        clock.advance(0.02)
    loop.submit(DriveCommand(0.2, -0.5, "test", clock.now()))
    loop.tick()
    left, right = loop.output
    assert left == 0.2  # slowing is immediate
    assert -0.1 < right < 0  # reversing starts again from zero


def test_coast_resets_the_ramp(loop, clock):
    for _ in range(20):
        loop.submit(DriveCommand(1.0, 1.0, "test", clock.now()))
        loop.tick()
        clock.advance(0.02)
    clock.advance(1.0)  # command goes stale: coast
    loop.tick()
    assert loop.stale and loop.output == (0.0, 0.0)
    loop.submit(DriveCommand(1.0, 1.0, "test", clock.now()))
    loop.tick()
    assert loop.output[0] < 0.1
