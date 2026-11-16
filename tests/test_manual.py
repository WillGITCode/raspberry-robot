import itertools

import pytest

from rover.manual import BOOST_CAP, INNER_DROP, SPEED_CAP, manual_command
from rover.pad import PadState


def cmd(**k):
    c = manual_command(PadState(**k), 0.0)
    return c.left, c.right


def test_forward_equal_at_cap():
    c = manual_command(PadState(ly=1.0), 0.0)
    assert c.left == c.right == SPEED_CAP and c.source == "person"


def test_trigger_raises_cap():
    assert cmd(ly=1.0, trigger=1.0) == (1.0, 1.0)


def test_deadzone_input_gives_zero():
    assert cmd() == (0.0, 0.0)


def test_turn_spins_in_place():
    assert cmd(rx=1.0) == (SPEED_CAP, -SPEED_CAP)


def test_full_left_outer_full_inner_slower():
    # Boss: full left gives the opposite side full speed forward, the same side slower (half at first,
    # then sharper after the floor run: INNER_DROP 0.7, the inner side at 30%)
    inner = 1.0 - INNER_DROP
    assert cmd(lx=-1.0) == pytest.approx((inner * SPEED_CAP, SPEED_CAP))
    assert cmd(lx=1.0) == pytest.approx((SPEED_CAP, inner * SPEED_CAP))
    assert cmd(lx=-1.0, ly=1.0) == pytest.approx((inner * SPEED_CAP, SPEED_CAP))


def test_steering_is_proportional():
    left, right = cmd(lx=-0.5)
    assert right == pytest.approx(0.5 * SPEED_CAP)  # speed follows the push
    assert left == pytest.approx(0.5 * (1 - INNER_DROP * 0.5) * SPEED_CAP)  # inner side drops by INNER_DROP * |lx|
    assert cmd(lx=-0.2, ly=1.0) == pytest.approx(((1 - INNER_DROP * 0.2) * SPEED_CAP, SPEED_CAP))


def test_sideways_pulled_back_is_slow_reverse_only():
    left, right = cmd(lx=-1.0, ly=-0.2)
    assert -0.2 * SPEED_CAP <= left < 0 and -0.2 * SPEED_CAP <= right < 0


def test_reverse_arcs_like_a_car():
    left, right = cmd(lx=-1.0, ly=-1.0)
    assert right == pytest.approx(-SPEED_CAP) and left == pytest.approx(-(1 - INNER_DROP) * SPEED_CAP)


def test_no_side_passes_the_cap():
    vals = (-1.0, -0.6, -0.1, 0.0, 0.3, 1.0)
    for ly, lx, rx, trig in itertools.product(vals, vals, vals, (0.0, 1.0)):
        cap = BOOST_CAP if trig else SPEED_CAP
        left, right = cmd(ly=ly, lx=lx, rx=rx, trigger=trig)
        assert abs(left) <= cap + 1e-9 and abs(right) <= cap + 1e-9
