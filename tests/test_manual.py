from rover.manual import SPEED_CAP, manual_command
from rover.pad import PadState


def test_forward_equal_at_cap():
    c = manual_command(PadState(ly=1.0), 0.0)
    assert c.left == c.right == SPEED_CAP and c.source == "person"


def test_trigger_raises_cap():
    c = manual_command(PadState(ly=1.0, trigger=1.0), 0.0)
    assert c.left == c.right == 1.0


def test_deadzone_input_gives_zero():
    c = manual_command(PadState(), 0.0)
    assert c.left == 0.0 and c.right == 0.0


def test_turn_spins_in_place():
    c = manual_command(PadState(rx=1.0), 0.0)
    assert c.left == SPEED_CAP and c.right == -SPEED_CAP
