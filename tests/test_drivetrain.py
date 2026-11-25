"""The motor-control layer on fake parts: spike filter, speed PI, encoder fault, moves."""
import math

import pytest

from rover import drivetrain
from rover.command import DriveCommand
from rover.control import Arbiter
from rover.drive_input import DriveInput, MoveRequest
from rover.drivetrain import Drivetrain
from rover.encoders import FakeEncoders, SpikeFilter
from rover.loop import FakeClock
from rover.move import Mover, mix
from rover.odometry import Odometry


class Log:
    def __init__(self):
        self.items = []

    def emit(self, event, **f):
        self.items.append((event, f))

    def names(self):
        return [n for n, _ in self.items]


class Plant:
    """Two wheels: edges per second = gain x duty x (top speed / metres per edge). Gains differ per side."""

    def __init__(self, gains=(1.0, 1.0)):
        self.gains, self.carry = gains, [0.0, 0.0]

    def edges(self, duty, dt):
        out = []
        for i, d in enumerate(duty):
            self.carry[i] += abs(d) * self.gains[i] * drivetrain.MAX_SPEED_MPS / drivetrain.M_PER_EDGE_LEFT * dt
            n = int(self.carry[i])
            self.carry[i] -= n
            out.append(n)
        return tuple(out)


def run(dt_, targets, plant, seconds, edges=None, log=None):
    clock, duty = 0.0, (0.0, 0.0)
    dr = Drivetrain(log, closed_loop=True)
    speeds = []
    for _ in range(int(seconds / 0.02)):
        clock += 0.02
        duty = dr.duty(clock, targets, plant.edges(duty, 0.02))
        speeds.append(dr.speed)
    return dr, duty, speeds


def test_spike_filter_drops_edges_closer_than_the_minimum():
    enc = FakeEncoders()
    enc.add_edges(0, [0.100, 0.1005, 0.101, 0.104, 0.1042])  # 0.1005, 0.101 and 0.1042 are noise
    enc.add_edges(1, [0.100, 0.1005])  # each side has its own last edge
    assert enc.read() == (2, 1) and enc.filter.dropped == [3, 1]
    assert SpikeFilter(0.0).accept(0, 1.0) and SpikeFilter(0.0).accept(0, 1.0)


def test_pi_makes_both_sides_reach_the_target_speed_with_unequal_motors():
    dr, duty, speeds = run(0.02, (0.5, 0.5), Plant(gains=(0.8, 1.0)), 6.0)
    want = 0.5 * drivetrain.MAX_SPEED_MPS
    assert all(abs(s - want) < 0.03 for s in speeds[-1]), speeds[-1]
    assert duty[0] > duty[1] and dr.fault is None  # the weak side got more duty


def test_pi_output_is_clamped_and_keeps_the_direction():
    dr = Drivetrain(closed_loop=True)
    for i in range(1, 40):  # asked for speed, wheel never turns: the correction stays bounded
        duty = dr.duty(i * 0.02, (-0.5, 0.5), (0, 0))
    assert duty[0] == pytest.approx(-(0.5 + drivetrain.MAX_CORRECTION)) and duty[1] > 0 and dr.fault is None


def test_open_loop_without_encoders_is_duty_with_trim(monkeypatch):
    monkeypatch.setattr(drivetrain, "TRIM", 0.1)
    dr = Drivetrain(closed_loop=False)
    left, right = dr.duty(1.0, (0.5, 0.5), None)
    assert left == pytest.approx(0.45) and right == pytest.approx(0.55)
    assert dr.duty(1.02, (1.0, -1.0), None) == (pytest.approx(0.9), pytest.approx(-1.0))


def test_a_driven_side_with_no_edges_is_an_encoder_fault():
    log = Log()
    dr = Drivetrain(log, closed_loop=True)
    for i in range(1, 100):
        duty = dr.duty(i * 0.02, (0.6, 0.6), (2, 0))  # the right encoder is dead
        if dr.fault:
            break
    assert dr.fault == ("right", "no_edges") and duty == (0.0, 0.0)
    assert "encoder_fault" in log.names()
    assert dr.duty(5.0, (0.6, 0.6), (2, 2)) == (0.0, 0.0)  # latched, whatever the edges say
    dr.rearm()
    assert dr.fault is None and dr.duty(5.02, (0.6, 0.6), (2, 2))[0] > 0


def test_a_slow_command_with_no_edges_is_not_a_fault():
    dr = Drivetrain(closed_loop=True)
    for i in range(1, 300):
        dr.duty(i * 0.02, (0.1, 0.1), (0, 0))
    assert dr.fault is None  # below fault_duty


def test_an_impossible_edge_rate_is_an_encoder_fault():
    dr = Drivetrain(Log(), closed_loop=True)
    for i in range(1, 40):
        dr.duty(i * 0.02, (0.3, 0.3), (0, 12))  # 600 edges/s on the right
        if dr.fault:
            break
    assert dr.fault == ("right", "edge_rate")


def test_the_loop_coasts_on_an_encoder_fault_and_the_stop_outranks_the_command(motors, pins):
    from rover.loop import TickLoop

    clock, enc = FakeClock(), FakeEncoders()
    dr = Drivetrain(Log(), closed_loop=True)
    loop = TickLoop(motors, clock, drivetrain=dr)
    for _ in range(100):
        clock.advance(0.02)
        loop.edges = (2, 0)
        loop.submit(DriveCommand(0.7, 0.7, "bench", clock.now()))
        loop.tick()
        if dr.fault:
            break
    assert dr.fault and loop.output == (0.0, 0.0)
    assert pins(18).state == 0 and pins(32).state == 0  # the left side coasts too


def test_mix_turns_counter_clockwise_and_scales_down_together():
    assert mix(0.3, 0.0) == (0.3, 0.3)
    assert mix(0.0, 0.45) == (-0.45, 0.45)
    left, right = mix(0.9, 0.3)
    assert (left, right) == (pytest.approx(0.6 / 1.2), 1.0)


def drive_move(mover, odo, step, seconds=20.0):
    now, cmds = 0.0, []
    while now < seconds:
        cmd = mover.tick(now, odo)
        if cmd is None:
            break
        cmds.append(cmd)
        step(cmd, odo)
        now += 0.02
    return now, cmds


def straight(cmd, odo):
    odo.update((int(abs(cmd.left) * 4), int(abs(cmd.right) * 4)), (cmd.left, cmd.right), 0.02)


def spin(cmd, odo):
    odo.update((0, 0), (cmd.left, cmd.right), 0.02, yaw_rate=(cmd.right - cmd.left) * 2.0)


def test_distance_stops_at_the_distance_and_backs_up_on_a_negative_one():
    odo, mover = Odometry(), Mover()
    mover.distance(0.5)
    drive_move(mover, odo, straight)
    assert mover.reason == "distance" and 0.5 <= odo.x < 0.56
    mover.distance(-0.2)
    drive_move(mover, odo, straight)
    assert mover.reason == "distance" and 0.28 < odo.x < 0.32


def test_turn_stops_at_the_angle_either_way():
    odo, mover = Odometry(), Mover()
    mover.turn(90)
    drive_move(mover, odo, spin)
    assert mover.reason == "angle" and math.degrees(odo.heading) == pytest.approx(90, abs=6)
    mover.turn(-180)
    drive_move(mover, odo, spin)
    assert mover.reason == "angle" and math.degrees(odo.heading) == pytest.approx(-90, abs=6)


def test_every_move_ends_at_its_time_cap_or_distance_cap():
    odo, mover = Odometry(), Mover()
    mover.drive(0.3, 0.0, seconds=1.0)  # the robot does not move: the time cap ends it
    now, _ = drive_move(mover, odo, lambda c, o: None)
    assert mover.reason == "time" and now == pytest.approx(1.0, abs=0.03)
    mover.turn(90)  # no heading source: the time cap too, never a spin for ever
    drive_move(mover, odo, lambda c, o: None)
    assert mover.reason == "time"
    mover.drive(0.5, 0.0, metres=0.2, seconds=30)
    drive_move(mover, odo, straight)
    assert mover.reason == "distance_cap" and odo.distance < 0.3
    with pytest.raises(ValueError):
        mover.distance(50)
    with pytest.raises(ValueError):
        mover.drive(1.5)


def test_the_arbiter_runs_a_bench_move_and_the_stop_latch_ends_it():
    from rover.modes import ModeManager, Sense
    from rover.pad import PadState

    log = Log()
    a = Arbiter(log, None)
    odo = Odometry()
    a.receive(MoveRequest("distance", (0.3,), "bench", 0.0), 0.0)
    cmd = a.decide(0.0, None, Sense(), odo)
    assert cmd.left == cmd.right > 0 and a.source == "bench_move"
    a.receive(DriveCommand(0.0, 0.0, "bench", 0.1), 0.1)  # a plain drive replaces the move
    assert a.mover.done and a.decide(0.1, None, Sense(), odo).source == "bench"

    b = Arbiter(log, ModeManager(log))
    b.manager.latched = False
    b.receive(MoveRequest("turn", (90.0,), "bench", 0.0), 0.0)
    b.decide(0.0, PadState(back=True), Sense(), odo)
    assert b.mover.done and b.decide(0.02, PadState(), Sense(), odo) is None  # Back latched: nothing drives
    b.receive(MoveRequest("turn", (90.0,), "bench", 0.1), 0.1)
    assert b.mover.done and ("bench_refused", {"reason": "latched"}) in log.items


def test_drive_input_parses_move_lines_and_rejects_bad_ones(tmp_path):
    import socket

    path = str(tmp_path / "d.sock")
    inp = DriveInput(path, FakeClock())
    tx = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
    for line in (b"move distance 0.5", b"move turn 90 0.5", b"move drive 0.3 0.1 2", b"move fly 1", b"move distance"):
        tx.sendto(line, path)
    got = inp.poll()
    assert [type(g).__name__ for g in got] == ["MoveRequest"] * 3 + ["ValueError"] * 2
    assert got[2].args == (0.3, 0.1, 2.0)
    inp.close()


def test_robot_latches_the_stop_on_an_encoder_fault_and_start_rearms_it(motors, monkeypatch):
    from rover.encoders import FakeEncoders
    from rover.events import Events
    from rover.main import serve
    from rover.odometry import PoseTracker
    from rover.pad import PadState
    from tests.test_main import FakeNotifier, ScriptedInput

    import io

    monkeypatch.setattr(drivetrain, "FAULT_DUTY", 0.2)  # the blind guard caps the pad at 0.3
    clock, enc, log = FakeClock(), FakeEncoders(), io.StringIO()
    events = Events(log, clock)
    pose = PoseTracker(enc, None)

    class Pad:
        def poll(self):
            t = clock.now()
            return PadState(start=0.1 < t < 0.2 or 3.0 < t < 3.1, ly=0.8 if t > 0.3 else 0.0)

    def sleep(s):
        clock.advance(0.02)

    serve(motors, clock, FakeNotifier(), events, ScriptedInput({}), ticks=200, sleep=sleep, pad=Pad(), pose=pose)
    text = log.getvalue()
    assert text.index('"encoder_fault"') < text.index('"encoder_rearm"')  # fault at ~1.3 s, Start at 3.0 s
    assert '"source": "encoder_fault"' in text and text.count('"to": "manual"') == 2
