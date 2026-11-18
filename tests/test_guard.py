import pytest

from rover.guard import BLIND_CAP, MEMORY_S, ObstacleGuard, speed_limit
from rover.scanner import Reading
from rover.servo import AHEAD


class StubScanner:
    def __init__(self):
        self.reading = None

    def ahead(self, now, max_age, window=20.0):
        r = self.reading
        return r if r is not None and now - r.time <= max_age else None


class Log:
    def __init__(self):
        self.items = []

    def emit(self, event, **f):
        self.items.append((event, f))


def at(d, t=0.0):
    return Reading(AHEAD, d, t)


def test_speed_limit_ramps_between_20_and_60_cm():
    assert speed_limit(0.10) == 0.0 and speed_limit(0.20) == 0.0
    assert speed_limit(0.40) == pytest.approx(0.5)
    assert speed_limit(0.60) == 1.0 and speed_limit(3.0) == 1.0
    assert speed_limit(0.23) == 0.0 and speed_limit(0.25) > 0.1  # under MIN_MOVE snaps to a stop


def test_forward_limited_reverse_and_spin_free():
    sc = StubScanner()
    g = ObstacleGuard(sc, Log())
    sc.reading = at(0.10)
    assert g.limit(0.3, 0.3, 0.0) == (0.0, 0.0)  # stop at the wall
    assert g.limit(-0.3, -0.3, 0.0) == (-0.3, -0.3)  # backing off is free
    assert g.limit(0.3, -0.3, 0.0) == (0.3, -0.3)  # spin in place is free
    left, right = g.limit(0.15, 0.3, 0.0)  # a forward arc keeps its turn
    assert (left, right) == pytest.approx((-0.075, 0.075))
    sc.reading = at(0.40)
    assert g.limit(1.0, 1.0, 0.0) == pytest.approx((0.5, 0.5))
    assert g.limit(0.3, 0.3, 0.0) == (0.3, 0.3)  # under the limit: untouched


def test_no_reading_caps_forward_and_remembers_a_close_one():
    sc = StubScanner()
    g = ObstacleGuard(sc, Log())
    assert g.limit(1.0, 1.0, 0.0) == (BLIND_CAP, BLIND_CAP)  # never "clear"
    sc.reading = at(0.25, t=1.0)
    g.limit(0.3, 0.3, 1.0)
    sc.reading = None  # the sensor fails right after a close reading
    left, _ = g.limit(1.0, 1.0, 1.2)
    assert left == pytest.approx(speed_limit(0.25)) and g.state == "blind"
    assert g.limit(1.0, 1.0, 1.0 + MEMORY_S + 0.1) == (BLIND_CAP, BLIND_CAP)


def test_state_changes_are_logged_once_they_hold():
    sc, log = StubScanner(), Log()
    g = ObstacleGuard(sc, log)
    t = 0.0
    for d in (1.0, 0.4, 0.1, 1.0):  # each held for 0.3 s at 50 Hz
        for _ in range(15):
            sc.reading = at(d, t)
            g.limit(0.3, 0.3, t)
            t += 0.02
    assert [f["state"] for _, f in log.items] == ["clear", "slow", "stop", "clear"]
    assert all(e == "obstacle_limit" for e, _ in log.items)


def test_flapping_is_applied_but_not_logged_every_tick():
    sc, log = StubScanner(), Log()
    g = ObstacleGuard(sc, log)
    t, states = 0.0, set()
    for i in range(50):  # two echoes, 48 and 72 cm, alternating every tick for 1 s
        sc.reading = at(0.48 if i % 2 else 0.72, t)
        g.limit(1.0, 1.0, t)
        states.add(g.state)
        t += 0.02
    assert states == {"slow", "clear"}  # the limit still follows every tick
    assert len(log.items) <= 1  # the log does not


def test_stop_is_logged_at_once():
    sc, log = StubScanner(), Log()
    g = ObstacleGuard(sc, log)
    sc.reading = at(0.1)
    g.limit(0.3, 0.3, 0.0)
    assert log.items[-1][1]["state"] == "stop"


def test_no_scanner_is_blind():
    g = ObstacleGuard(None)
    assert g.limit(1.0, 1.0, 0.0) == (BLIND_CAP, BLIND_CAP) and g.state == "blind"


def test_nothing_is_logged_while_standing_still():
    sc, log = StubScanner(), Log()
    g = ObstacleGuard(sc, log)
    t = 0.0
    for d in (1.0, 0.4, None, 0.1):  # states change, but the command is 0,0 (e.g. explore looking)
        for _ in range(15):
            sc.reading = None if d is None else at(d, t)
            g.limit(0.0, 0.0, t)
            g.limit(0.3, -0.3, t)  # spinning in place: no forward motion either
            t += 0.02
    assert log.items == []
    sc.reading = at(0.1, t)
    g.limit(0.3, 0.3, t)
    assert log.items[-1][1]["state"] == "stop"
