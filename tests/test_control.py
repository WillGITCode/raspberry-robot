"""The arbiter's one priority rule, without the loop: stop, then people, then agents (the bench)."""
from rover.command import DriveCommand
from rover.control import Arbiter
from rover.drive_input import ModeRequest
from rover.modes import ModeManager, Sense
from rover.pad import PadState

REST, START, Y, BACK = PadState(), PadState(start=True), PadState(y=True), PadState(back=True)


class Log:
    def __init__(self):
        self.items = []

    def emit(self, event, **f):
        self.items.append((event, f))

    def mode_change(self, old, new, source):
        self.items.append(("mode_change", {"from": old, "to": new, "source": source}))


def bench(left=0.4, right=0.4, t=0.0):
    return DriveCommand(left, right, "bench", t)


def test_the_bench_drives_only_while_people_give_no_command():
    a = Arbiter(Log(), ModeManager(Log()))
    a.receive(bench(), 0.0)
    assert a.decide(0.0, REST, Sense()) is None and a.bench_drive is None  # pad latched: refused (GH #29)
    a.receive(bench(), 0.01)
    a.decide(0.02, START, Sense())  # people arm the pad: manual
    cmd = a.decide(0.04, REST, Sense())
    assert cmd.source == "person" and (cmd.left, cmd.right) == (0.0, 0.0) and a.source == "pad"


def test_a_latched_pad_ends_a_bench_mode_and_drive():
    log = Log()
    a = Arbiter(log, ModeManager(log))
    a.receive(ModeRequest("explore", 10.0, "bench", 0.0), 0.0)
    assert a.mode_name == "bench:explore"
    assert a.decide(0.02, REST, Sense()) is None and a.source is None
    assert a.bench is None and a.mode_name == "idle"
    assert [f.get("reason") for e, f in log.items if e == "bench_mode"][-1] == "latched"
    a.decide(0.04, START, Sense())
    a.decide(0.06, BACK, Sense())  # Back latches again
    a.receive(bench(), 0.08)
    assert a.decide(0.08, REST, Sense()) is None and a.bench_drive is None
    assert any(e == "bench_refused" for e, _ in log.items)


def test_bench_items_replace_each_other():
    log = Log()
    a = Arbiter(log, None)  # no pad at all
    a.receive(ModeRequest("explore", 10.0, "bench", 0.0), 0.0)
    a.receive(bench(), 0.1)  # a drive replaces the mode
    assert a.bench is None and a.decide(0.1, None, None).left == 0.4
    a.receive(ModeRequest("explore", 10.0, "bench", 0.2), 0.2)  # a mode clears the drive
    assert a.bench_drive is None and a.bench is not None
    a.receive(ModeRequest("idle", 10.0, "bench", 0.3), 0.3)
    assert a.bench is None and a.decide(0.3, None, None) is None
    reasons = [f.get("reason") for e, f in log.items if e == "bench_mode" and f.get("mode") is None]
    assert reasons == ["drive", "idle"]


def test_the_bench_can_not_run_manual_or_unknown_modes():
    log = Log()
    a = Arbiter(log, None)
    a.receive(ModeRequest("manual", 5.0, "bench", 0.0), 0.0)
    a.receive(ModeRequest("dance", 5.0, "bench", 0.0), 0.0)
    assert a.bench is None
    assert [f["error"] for e, f in log.items if e == "fault"] == [
        "bench cannot run mode 'manual'", "bench cannot run mode 'dance'"]


def test_a_bad_socket_line_is_a_fault():
    log = Log()
    Arbiter(log, None).receive(ValueError("could not convert string to float: 'x'"), 0.0)
    assert log.items[0][0] == "fault" and "bad drive input" in log.items[0][1]["error"]
