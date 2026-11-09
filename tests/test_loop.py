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
