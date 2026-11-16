import io
import json
import math

from rover.events import Events
from rover.explore import ExploreMode, choose_side
from rover.loop import FakeClock
from rover.main import serve
from rover.modes import Inputs, ModeManager, Sense
from rover.pad import PadState
from rover.scanner import Reading, Scanner
from rover.servo import FakeServo
from rover.sim import Sim, SimMotors, SimPing
from tests.test_main import FakeNotifier, ScriptedInput, ScriptedPad

REST, START, Y = PadState(), PadState(start=True), PadState(y=True)


class Log:
    def __init__(self):
        self.items = []

    def emit(self, event, **f):
        self.items.append((event, f))

    def mode_change(self, old, new, source):
        self.items.append(("mode_change", {"from": old, "to": new, "source": source}))


def test_choose_side_turns_toward_the_room():
    r = lambda a, d: Reading(a, d, 0.0)  # noqa: E731
    assert choose_side([r(10, 2.0), r(170, 0.5)]) == 1  # 10 degrees is left
    assert choose_side([r(10, 0.3), r(170, 1.5)]) == -1
    assert choose_side([]) == 1
    assert choose_side([r(10, None), r(170, None)]) == 1


def test_y_starts_explore_only_when_armed_and_sticks_take_over():
    log = Log()
    m = ModeManager(log)
    m.update(Y, 0.0)
    assert m.name == "idle"  # latched: Y alone never starts motion
    m.update(START, 0.1)
    m.update(REST, 0.2)
    m.update(Y, 0.3)
    assert m.name == "explore"
    m.update(PadState(ly=0.5), 0.4)
    assert m.name == "manual"  # people beat the robot
    m.update(Y, 0.5)
    m.update(REST, 0.6)
    m.update(PadState(back=True), 0.7)
    assert m.name == "idle" and m.latched
    sources = [f["source"] for e, f in log.items if e == "mode_change"]
    assert sources == ["start", "y", "sticks", "y", "back"]


def test_explore_waits_when_blind_and_gives_up_to_idle():
    log = Log()
    m = ModeManager(log)
    m.update(START, 0.0)
    m.update(Y, 0.1)
    t = 0.1
    while t < 7.0 and m.name == "explore":
        t += 0.02
        cmd = m.update(REST, t, Sense(ahead=None))
        assert cmd is None or (cmd.left, cmd.right) == (0.0, 0.0)  # never drives blind
    assert m.name == "idle"
    states = [f.get("state") for e, f in log.items if e == "explore"]
    assert states[:2] == ["cruise", "wait"]


def test_explore_turns_toward_the_open_side():
    mode, log = ExploreMode(), Log()
    mode.events = log
    near = Reading(95.0, 0.3, 0.0)
    mode.tick(Inputs(REST, 0.0, Sense(ahead=near)))  # cruise -> sees 30 cm -> look
    mode.tick(Inputs(REST, 0.02, Sense(ahead=near)))
    assert mode.state == "look" and mode.scan == "sweep"
    sweep = tuple(Reading(a, 2.0 if a > 95 else 0.4, 0.5) for a in range(10, 171, 20))
    cmd = mode.tick(Inputs(REST, 1.6, Sense(ahead=near, readings=sweep)))
    assert mode.state == "turn" and mode.turn_dir == -1  # more room on the right
    cmd = mode.tick(Inputs(REST, 1.62, Sense(ahead=near, readings=sweep)))
    assert cmd.left > 0 > cmd.right  # spinning right in place


import pytest  # noqa: E402


@pytest.mark.parametrize("x,y,heading,width,height", [
    (1.0, 2.5, 0.3, 5.0, 4.0), (0.5, 0.5, 0.8, 3.0, 3.0), (2.0, 1.0, 2.0, 6.0, 2.0)])
def test_explores_a_room_in_the_sim_without_touching_a_wall(motors, x, y, heading, width, height):
    clock, out = FakeClock(), io.StringIO()
    sim = Sim(x=x, y=y, heading=heading, width=width, height=height, max_speed=0.5)
    sim_motors, servo = SimMotors(), FakeServo()
    scanner = Scanner(SimPing(sim, servo, clock), servo)
    pad = ScriptedPad({0: REST, 2: START, 3: REST, 5: Y, 6: REST})
    closest, path, last = 10.0, 0.0, (sim.x, sim.y)

    def sleep(s):
        nonlocal closest, path, last
        sim.step(sim_motors.left, sim_motors.right, 0.02)
        clock.advance(0.02)
        closest = min(closest, sim.x, sim.y, sim.width - sim.x, sim.height - sim.y)
        path += math.dist(last, (sim.x, sim.y))
        last = (sim.x, sim.y)

    serve(sim_motors, clock, FakeNotifier(), Events(out, clock), ScriptedInput({}), ticks=6000,
          sleep=sleep, pad=pad, scanner=scanner)  # 2 minutes
    events = [json.loads(x) for x in out.getvalue().splitlines()]
    looks = [e for e in events if e["event"] == "explore" and e["state"] == "look"]
    modes = [(e["from"], e["to"]) for e in events if e["event"] == "mode_change"]
    assert modes == [("idle", "manual"), ("manual", "explore")]  # still exploring after 2 minutes
    assert closest > 0.18, closest  # never touched a wall (the fan catches shallow walls)
    assert path > 12.0, path  # it really moved around the room
    assert len(looks) >= 3  # and turned away from walls several times
