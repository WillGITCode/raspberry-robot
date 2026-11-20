import itertools

import pytest

from rover.manual import BOOST_CAP, INNER_DROP, SPEED_CAP, TURN_CAP, manual_command
from rover.pad import PadState


def cmd(**k):
    c = manual_command(PadState(**k), 0.0)
    return c.left, c.right


def test_forward_equal_at_cap():
    c = manual_command(PadState(ly=1.0), 0.0)
    assert c.left == c.right == SPEED_CAP and c.source == "person"


def test_trigger_raises_cap():
    assert cmd(ly=1.0, trigger=1.0) == (BOOST_CAP, BOOST_CAP)
    assert BOOST_CAP <= 0.85  # at full duty the motors' noise blinds the ping (stand test)


def test_deadzone_input_gives_zero():
    assert cmd() == (0.0, 0.0)


def test_turn_spins_in_place():
    assert cmd(rx=1.0) == (SPEED_CAP, -SPEED_CAP)


def test_full_left_outer_full_inner_slower():
    # Boss: full left gives the opposite side full speed forward, the same side slower (half at first,
    # then sharper after the floor run: INNER_DROP 0.7, the inner side at 30%)
    # then far sharper (2026-11-20): INNER_DROP 1.3, the inner side turns back at 30%, the outer runs at TURN_CAP
    inner = 1.0 - INNER_DROP
    assert inner < 0
    assert cmd(lx=-1.0) == pytest.approx((inner * TURN_CAP, TURN_CAP))
    assert cmd(lx=1.0) == pytest.approx((TURN_CAP, inner * TURN_CAP))
    assert cmd(lx=-1.0, ly=1.0) == pytest.approx((inner * TURN_CAP, TURN_CAP))


def test_steering_is_proportional():
    left, right = cmd(lx=-0.5)
    cap = SPEED_CAP + (TURN_CAP - SPEED_CAP) * 0.5  # the outer cap rises with |lx|
    assert right == pytest.approx(0.5 * cap)  # speed follows the push
    assert left == pytest.approx(0.5 * (1 - INNER_DROP * 0.5) * cap)  # inner side drops by INNER_DROP * |lx|
    cap = SPEED_CAP + (TURN_CAP - SPEED_CAP) * 0.2
    assert cmd(lx=-0.2, ly=1.0) == pytest.approx(((1 - INNER_DROP * 0.2) * cap, cap))


def test_sideways_pulled_back_is_slow_reverse_only():
    left, right = cmd(lx=-1.0, ly=-0.2)
    assert -0.2 * TURN_CAP <= right < 0 and abs(left) <= 0.2 * TURN_CAP


def test_reverse_arcs_like_a_car():
    left, right = cmd(lx=-1.0, ly=-1.0)
    assert right == pytest.approx(-TURN_CAP) and left == pytest.approx(-(1 - INNER_DROP) * TURN_CAP)


def test_no_side_passes_the_cap():
    vals = (-1.0, -0.6, -0.1, 0.0, 0.3, 1.0)
    for ly, lx, rx, trig in itertools.product(vals, vals, vals, (0.0, 1.0)):
        cap = max(BOOST_CAP if trig else SPEED_CAP, TURN_CAP if lx else 0.0)
        left, right = cmd(ly=ly, lx=lx, rx=rx, trigger=trig)
        assert abs(left) <= cap + 1e-9 and abs(right) <= cap + 1e-9
