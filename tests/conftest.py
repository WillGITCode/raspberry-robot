import os

os.environ.setdefault("GPIOZERO_PIN_FACTORY", "mock")
os.environ.setdefault("GPIOZERO_MOCK_PIN_CLASS", "mockpwmpin")

import time  # noqa: E402

import pytest  # noqa: E402
from gpiozero import Device  # noqa: E402

from rover.loop import FakeClock, TickLoop  # noqa: E402
from rover.motors import Motors  # noqa: E402


@pytest.fixture
def pins():
    yield lambda n: Device.pin_factory.pin(f"BOARD{n}")
    Device.pin_factory.reset()


@pytest.fixture
def motors(pins):
    m = Motors()
    yield m
    m.close()


@pytest.fixture
def clock():
    return FakeClock()


@pytest.fixture
def loop(motors, clock):
    return TickLoop(motors, clock)


@pytest.fixture
def no_sleep(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("time.sleep called inside tick()")

    monkeypatch.setattr(time, "sleep", boom)
