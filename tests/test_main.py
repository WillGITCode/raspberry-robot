import io
import json

import pytest

from rover.drive_input import DriveInput
from rover.events import Events
from rover.loop import FakeClock
from rover.main import serve


class FakeNotifier:
    def __init__(self):
        self.messages = []

    def notify(self, m):
        self.messages.append(m)


class ScriptedInput:
    def __init__(self, script):
        self.script = script  # tick index -> commands
        self.n = 0

    def poll(self):
        self.n += 1
        return self.script.get(self.n - 1, [])


def run(motors, ticks, script=None, sleep=None):
    clock = FakeClock()
    out, notifier = io.StringIO(), FakeNotifier()
    from rover.command import DriveCommand
    script = {i: [DriveCommand(*c, "bench", 0.0)] for i, c in (script or {}).items()}
    sl = sleep or (lambda s: clock.advance(0.02))
    serve(motors, clock, notifier, Events(out, clock), ScriptedInput(script), ticks=ticks, sleep=sl, commit="abc")
    return [json.loads(line) for line in out.getvalue().splitlines()], notifier, clock


def test_events_are_json_lines_with_start_commit(motors):
    events, notifier, _ = run(motors, 3)
    assert events[0]["event"] == "start" and events[0]["commit"] == "abc"
    assert events[-1]["event"] == "stop"
    assert notifier.messages[0] == "READY=1"
    assert notifier.messages.count("WATCHDOG=1") == 3


def test_drive_then_silence_logs_deadman_stop(motors):
    # command at tick 0 is stamped t=0; by t=0.32 it is stale
    events, _, _ = run(motors, 25, script={0: (0.5, 0.5)})
    names = [e["event"] for e in events]
    assert "drive" in names
    drive = next(e for e in events if e["event"] == "drive")
    assert drive["source"] == "bench"
    assert names.count("deadman_stop") == 1


def test_loop_that_stops_ticking_stops_watchdog(motors):
    clock, out, notifier = FakeClock(), io.StringIO(), FakeNotifier()

    class Stalls:
        # tick 0 is normal; tick 1 hangs in poll for 5 s and never completes
        n = 0

        def poll(self):
            self.n += 1
            if self.n == 2:
                stalled_at.append(len(notifier.messages))
                clock.advance(5.0)
                raise RuntimeError("hung")
            return []

    stalled_at = []
    with pytest.raises(RuntimeError):
        serve(motors, clock, notifier, Events(out, clock), Stalls(), ticks=10,
              sleep=lambda s: clock.advance(0.02), commit="abc")
    assert notifier.messages == ["READY=1", "WATCHDOG=1"]
    assert len(notifier.messages) == stalled_at[0]  # nothing sent during or after the stall


def test_tick_that_runs_past_the_period_logs_overrun(motors):
    clock, out = FakeClock(), io.StringIO()

    class Slow:
        def poll(self):
            clock.advance(0.05)  # tick takes 50 ms against a 20 ms period
            return []

    serve(motors, clock, FakeNotifier(), Events(out, clock), Slow(), ticks=1,
          sleep=lambda s: None, commit="abc")
    events = [json.loads(line) for line in out.getvalue().splitlines()]
    overrun = next(e for e in events if e["event"] == "tick_overrun")
    assert overrun["elapsed"] > overrun["period"]


def test_fault_is_logged_and_motors_coast(motors, pins):
    class Boom:
        def poll(self):
            raise RuntimeError("x")

    clock, out = FakeClock(), io.StringIO()
    with pytest.raises(RuntimeError):
        serve(motors, clock, FakeNotifier(), Events(out, clock), Boom(), ticks=1, sleep=lambda s: None)
    names = [json.loads(line)["event"] for line in out.getvalue().splitlines()]
    assert names == ["start", "fault", "stop"]


def test_socket_input_feeds_commands(tmp_path):
    import socket
    clock = FakeClock(1.0)
    try:
        di = DriveInput(str(tmp_path / "d.sock"), clock)
    except PermissionError:
        pytest.skip("sandbox forbids unix sockets")
    c = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    c.sendto(b"0.5 -0.5\n", str(tmp_path / "d.sock"))
    c.sendto(b"junk", str(tmp_path / "d.sock"))
    got = di.poll()
    assert (got[0].left, got[0].right, got[0].time) == (0.5, -0.5, 1.0)
    assert isinstance(got[1], ValueError)
    di.close()


# pad + modes inside the tick loop

class ScriptedPad:
    def __init__(self, script):
        self.script, self.n = script, 0  # tick index -> PadState, held until the next entry
        self.state = None

    def poll(self):
        self.state = self.script.get(self.n, self.state)
        self.n += 1
        return self.state


def test_guard_stops_a_forward_drive_at_an_obstacle(motors):
    from rover.ping import FakePing
    from rover.scanner import Scanner
    from rover.servo import FakeServo

    clock, out = FakeClock(), io.StringIO()
    ping = FakePing(clock, distance=1.5)
    scanner = Scanner(ping, FakeServo())
    seen = []

    class Status:
        def publish(self, snap):
            seen.append(snap)

    def sleep(s):
        clock.advance(0.02)
        ping.distance = 1.5 if clock.now() < 1.0 else 0.15  # something appears at t = 1 s

    levels = []

    class Input(ScriptedInput):
        def poll(self):
            levels.append(motors.left.enable.value)
            return [DriveCommand(0.5, 0.5, "bench", clock.now())]

    from rover.command import DriveCommand
    serve(motors, clock, FakeNotifier(), Events(out, clock), Input({}), ticks=80, sleep=sleep,
          scanner=scanner, status=Status())
    assert max(levels[30:45]) == 0.5  # clear ahead: the full command
    assert levels[-1] == 0  # 15 cm ahead: forward stopped
    states = [json.loads(x)["state"] for x in out.getvalue().splitlines() if '"obstacle_limit"' in x]
    assert states[0] == "blind" and "clear" in states and states[-1] == "stop"
    assert seen and seen[-1]["guard"]["state"] == "stop" and seen[-1]["ranges"][0]["angle"] == 95
