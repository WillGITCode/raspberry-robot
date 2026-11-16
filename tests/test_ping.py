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


def test_too_long_is_no_reading():
    e = echo_from_edges([(True, T0 + us(750)), (False, T0 + us(750) + us(25_000))], T0, 0.0)
    assert e.distance is None and e.error == "too_long"


def test_a_fall_too_soon_after_the_start_is_not_the_end():
    # a 50 us dip is noise: the echo goes on until the real fall
    edges = [(True, T0 + us(750)), (False, T0 + us(800))]
    assert echo_from_edges(edges, T0, 0.0) is None  # still waiting for the end
    end = T0 + us(750) + us(2900)
    edges.append((False, end))
    assert echo_from_edges(edges, T0, 0.0).distance == pytest.approx(width_to_distance(2900e-6))


def test_motor_noise_in_the_hold_off_is_ignored():
    edges = [(False, T0 + us(120)), (False, T0 + us(300)), (True, T0 + us(750)),
             (False, T0 + us(750) + us(2900))]
    assert echo_from_edges(edges, T0, 0.0).distance == pytest.approx(width_to_distance(2900e-6))


def test_a_start_named_falling_still_counts_as_the_start():
    # the kernel read the pin after a spike, so the echo's start came out "falling"
    edges = [(False, T0 + us(760)), (True, T0 + us(1500)), (False, T0 + us(760) + us(2900))]
    e = echo_from_edges(edges, T0, 0.0)
    assert e.distance == pytest.approx(width_to_distance(2900e-6)) and e.error is None


def test_a_lost_start_is_no_reading_never_a_guess():
    # only a late edge arrived: guessing the start read 1-2 m with an obstacle at 26 cm
    e = echo_from_edges([(False, T0 + us(750) + us(2900))], T0, 0.0)
    assert e.distance is None and e.error == "lost_start"


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
