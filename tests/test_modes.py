import io
import json

from rover.events import Events
from rover.loop import FakeClock
from rover.main import serve
from rover.pad import LOST, PadState
from tests.test_main import FakeNotifier, ScriptedInput, ScriptedPad

IDLE = PadState()
START = PadState(start=True)
FORWARD = PadState(ly=1.0)
BACK = PadState(back=True)



def test_start_stick_back_and_pad_loss(motors, pins):
    clock, out = FakeClock(), io.StringIO()
    pad = ScriptedPad({0: IDLE, 2: START, 3: FORWARD, 8: BACK, 9: FORWARD, 12: START, 13: FORWARD,
                       16: LOST, 17: FORWARD, 19: START, 20: FORWARD})
    log = []

    def sleep(s):
        log.append((pad.n - 1, motors.left.enable.value, motors.right.enable.value))
        clock.advance(0.02)

    serve(motors, clock, FakeNotifier(), Events(out, clock), ScriptedInput({}), ticks=23,
          sleep=sleep, pad=pad)
    en = {n: (l, r) for n, l, r in log}
    assert en[1] == (0, 0)  # idle until Start
    assert en[4] > (0, 0) and en[4][0] > 0 and en[4][1] > 0  # stick moves both enables
    assert en[9] == (0, 0) and en[10] == (0, 0)  # Back: idle, stick ignored
    assert en[13] > (0, 0)  # Start re-armed
    assert en[16] == (0, 0) and en[17] == (0, 0) and en[18] == (0, 0)  # pad lost
    assert en[21][0] > 0
    changes = [json.loads(x) for x in out.getvalue().splitlines() if '"mode_change"' in x]
    assert [(c["from"], c["to"], c["source"]) for c in changes] == [
        ("idle", "manual", "start"), ("manual", "idle", "back"), ("idle", "manual", "start"),
        ("manual", "idle", "pad_lost"), ("idle", "manual", "start")]
    assert all("t" in c for c in changes)


def test_never_moves_without_start(motors):
    clock, out = FakeClock(), io.StringIO()
    pad = ScriptedPad({0: FORWARD})
    levels = []
    serve(motors, clock, FakeNotifier(), Events(out, clock), ScriptedInput({}), ticks=5,
          sleep=lambda s: (levels.append(motors.left.enable.value), clock.advance(0.02)), pad=pad)
    assert levels == [0] * 5
    assert "mode_change" not in out.getvalue()
