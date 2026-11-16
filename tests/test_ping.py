import pytest

from rover.loop import FakeClock
from rover.ping import ECHO_TIMEOUT_S, FakePing, echo_from_edges, width_to_distance

T0 = 1_000_000_000  # trigger end, ns


def us(n):
    return int(n * 1000)


def test_one_metre_echo():
    width = 2 * 1.0 / 343.0  # seconds for 1 m and back
    edges = [(True, T0 + us(750)), (False, T0 + us(750) + int(width * 1e9))]
    e = echo_from_edges(edges, T0, 5.0)
    assert e.distance == pytest.approx(1.0, abs=1e-3) and e.error is None and e.time == 5.0


def test_still_waiting_gives_none():
    assert echo_from_edges([(True, T0 + us(750))], T0, 0.0) is None
    assert echo_from_edges([], T0, 0.0) is None


@pytest.mark.parametrize("edges,error", [
    ([(False, T0 + us(900))], "missed_rise"),  # echo began before the pin was an input
    ([(True, T0 + us(750)), (False, T0 + us(800))], "glitch"),
    ([(True, T0 + us(750)), (False, T0 + us(750) + us(25_000))], "too_long"),
])
def test_bad_echoes_are_no_reading(edges, error):
    e = echo_from_edges(edges, T0, 0.0)
    assert e.distance is None and e.error == error


def test_edges_before_the_trigger_are_ignored():
    width = us(2900)  # about 50 cm
    edges = [(False, T0 - us(100)), (True, T0 + us(750)), (False, T0 + us(750) + width)]
    assert echo_from_edges(edges, T0, 0.0).distance == pytest.approx(width_to_distance(width / 1e9))


def test_fake_answers_after_delay_and_times_out():
    clock = FakeClock()
    p = FakePing(clock, distance=0.5)
    assert p.trigger() and not p.trigger()  # one at a time
    assert p.poll() is None
    clock.advance(0.01)
    assert p.poll().distance == 0.5 and not p.busy
    p.distance = None
    p.trigger()
    clock.advance(0.01)
    assert p.poll() is None
    clock.advance(ECHO_TIMEOUT_S)
    e = p.poll()
    assert e.distance is None and e.error == "no_echo"
