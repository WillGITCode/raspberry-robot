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


def test_backs_off_when_cruising_gets_no_closer(motors):
    """Pushing on something the ping can't see: the wall ahead stops closing, so it backs off and looks."""
    clock, out = FakeClock(), io.StringIO()
    sim = Sim(x=1.0, y=1.0, heading=0.0, width=3.0, height=2.0, max_speed=0.5)  # wall 2 m ahead
    sim_motors, servo = SimMotors(), FakeServo()
    scanner = Scanner(SimPing(sim, servo, clock), servo)
    pad = ScriptedPad({0: REST, 2: START, 3: REST, 5: Y, 6: REST})

    def sleep(s):
        sim.stuck = 2.0 <= clock.now() < 6.5  # caught on something low for 4.5 s
        sim.step(sim_motors.left, sim_motors.right, 0.02)
        clock.advance(0.02)

    serve(sim_motors, clock, FakeNotifier(), Events(out, clock), ScriptedInput({}), ticks=500,
          sleep=sleep, pad=pad, scanner=scanner)
    steps = [(round(e["t"], 1), e["state"], e.get("reason")) for e in map(json.loads, out.getvalue().splitlines())
             if e["event"] == "explore"]
    backs = [s for s in steps if s[1] == "back"]
    assert backs and backs[0][2] == "stuck" and 5.0 <= backs[0][0] <= 6.0  # about 3 s after it stuck
    after = steps[steps.index(backs[0]) + 1]
    assert after[1] == "look" and after[2] == "backed_off"


def test_a_far_wall_is_never_stuck():
    mode = ExploreMode()
    far = Reading(95.0, 3.17, 0.0)  # the sensor's longest echo: open space
    for i in range(300):
        cmd = mode.tick(Inputs(REST, i * 0.02, Sense(ahead=far)))
    assert mode.state == "cruise" and cmd.left > 0


def test_moving_away_is_not_stuck():
    mode = ExploreMode()
    for i in range(300):  # 6 s, the reading ahead growing 1 cm a tick (veering away from something)
        mode.tick(Inputs(REST, i * 0.02, Sense(ahead=Reading(95.0, 0.6 + i * 0.006, i * 0.02))))
        assert mode.state == "cruise"


def _bench_run(motors, pad_script, inputs, ticks, distance=0.8):
    from rover.drive_input import ModeRequest
    from rover.ping import FakePing

    clock, out = FakeClock(), io.StringIO()
    servo = FakeServo()
    scanner = Scanner(FakePing(clock, distance=distance), servo)
    pad = ScriptedPad(pad_script)

    class Input(ScriptedInput):
        def poll(self):
            self.n += 1
            return [x(clock.now()) if callable(x) else x for x in self.script.get(self.n - 1, [])]

    req = lambda name, secs: (lambda t: ModeRequest(name, secs, "bench", t))  # noqa: E731
    script = {k: [req(*v) if isinstance(v, tuple) else v for v in vs] for k, vs in inputs.items()}
    levels = []

    def sleep(s):
        levels.append((motors.left.enable.value, motors.right.enable.value))
        clock.advance(0.02)

    serve(motors, clock, FakeNotifier(), Events(out, clock), Input(script), ticks=ticks, sleep=sleep,
          pad=pad, scanner=scanner)
    events = [json.loads(x) for x in out.getvalue().splitlines()]
    return events, levels


def test_bench_runs_explore_while_the_pad_is_idle_and_ends_it_at_the_deadline(motors):
    events, levels = _bench_run(motors, {0: REST}, {5: [("explore", 2.0)]}, ticks=200)
    bench = [e for e in events if e["event"] == "bench_mode"]
    assert bench[0]["mode"] == "explore" and bench[-1]["reason"] == "deadline"
    assert any(l > 0 for l, _ in levels[40:100])  # it cruised
    assert levels[-1] == (0, 0)  # and stopped after its 2 s
    assert not any(e["event"] == "mode_change" for e in events)  # the pad stayed idle and latched


def test_people_and_back_end_a_bench_mode(motors):
    events, _ = _bench_run(motors, {0: REST, 60: START, 61: REST}, {5: [("explore", 30.0)]}, ticks=100)
    assert [e for e in events if e["event"] == "bench_mode"][-1]["reason"] == "pad"
    events, _ = _bench_run(motors, {0: REST, 60: PadState(back=True), 61: REST}, {5: [("explore", 30.0)]},
                           ticks=100)
    assert [e for e in events if e["event"] == "bench_mode"][-1]["reason"] == "pad"


def test_bench_cannot_run_manual_and_mode_idle_ends_it(motors):
    events, _ = _bench_run(motors, {0: REST}, {5: [("manual", 5.0)], 10: [("explore", 5.0)],
                                               40: [("idle", 1.0)]}, ticks=60)
    assert any(e["event"] == "fault" and "manual" in e["error"] for e in events)
    assert [e for e in events if e["event"] == "bench_mode"][-1]["reason"] == "idle"


def test_mode_request_parsing():
    import os
    import socket
    import tempfile

    from rover.drive_input import DriveInput, ModeRequest

    path = os.path.join(tempfile.mkdtemp(), "drive.sock")
    di = DriveInput(path, FakeClock())
    s = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    for line in (b"mode explore 20", b"mode explore", b"mode explore 500", b"0.2 0.2"):
        s.sendto(line, path)
    got = di.poll()
    di.close()
    assert got[0] == ModeRequest("explore", 20.0, "bench", 0.0) and got[1].seconds == 10.0
    assert isinstance(got[2], ValueError) and got[3].left == 0.2


def test_turn_ends_only_once_ahead_stays_open():
    mode = ExploreMode()
    mode.state, mode.since, mode.turn_dir = "turn", 0.0, 1
    open_r = lambda t: Reading(95.0, 1.0, t)  # noqa: E731
    near_r = lambda t: Reading(95.0, 0.3, t)  # noqa: E731
    seq = [open_r, open_r, near_r] * 10 + [open_r] * 30  # open, but an obstacle keeps flicking back
    t = 0.4
    for i, r in enumerate(seq):
        mode.tick(Inputs(REST, t, Sense(ahead=r(t))))
        if i < 30:
            assert mode.state == "turn"  # never 0.3 s of open in the flicker
        t += 0.02
    assert mode.state == "cruise"
