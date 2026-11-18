import math

import pytest

from rover.encoders import M_PER_EDGE, FakeEncoders
from rover.imu import BiasCalibrator, FakeImu, to_signed
from rover.odometry import Odometry


def test_edge_length_from_the_measured_wheel():
    assert M_PER_EDGE == pytest.approx(math.pi * 0.065 / 20)  # about 10.2 mm


def test_straight_line_distance_and_direction_from_the_motor_sign():
    odo, enc = Odometry(), FakeEncoders()
    for _ in range(50):
        enc.add(2, 2)
        odo.update(enc.read(), (0.5, 0.5), 0.02)
    assert odo.x == pytest.approx(100 * M_PER_EDGE) and odo.y == pytest.approx(0.0)
    for _ in range(50):
        enc.add(2, 2)
        odo.update(enc.read(), (-0.5, -0.5), 0.02)
    assert odo.x == pytest.approx(0.0, abs=1e-9) and odo.distance == pytest.approx(200 * M_PER_EDGE)


def test_coasting_counts_keep_the_last_direction():
    odo = Odometry()
    odo.update((1, 1), (-0.4, -0.4), 0.02)
    odo.update((1, 1), (0.0, 0.0), 0.02)  # still rolling backward after the stop
    assert odo.x == pytest.approx(-2 * M_PER_EDGE)


def test_heading_from_the_gyro():
    odo = Odometry()
    for _ in range(50):  # 1 s at 90 deg/s, counter-clockwise, driving forward
        odo.update((1, 1), (0.3, 0.3), 0.02, yaw_rate=math.radians(90))
    assert math.degrees(odo.heading) == pytest.approx(90, abs=1e-6)
    assert odo.x > 0 and odo.y > 0  # a left arc


def test_heading_from_the_wheels_needs_a_track():
    no_track = Odometry()
    no_track.update((0, 4), (0.3, 0.3), 0.02)
    assert no_track.heading == 0.0  # no heading source: distance only
    odo = Odometry(track_m=0.2)
    odo.update((0, 4), (0.3, 0.3), 0.02)
    assert odo.heading == pytest.approx(4 * M_PER_EDGE / 0.2)


def test_gyro_bias_calibration_and_sign():
    imu = FakeImu(rate=0.0, bias=0.02)
    cal = BiasCalibrator(samples=10)
    while not cal.done:
        cal.add(imu.raw_yaw_rate())
    imu.bias = cal.bias
    assert imu.yaw_rate() == pytest.approx(0.0)
    assert to_signed(0xFF, 0x7F) == -129 and to_signed(0x00, 0x83) == 131


def test_pose_tracker_calibrates_while_still_then_tracks(motors):
    import io

    from rover.command import DriveCommand
    from rover.events import Events
    from rover.imu import BiasCalibrator
    from rover.loop import FakeClock
    from rover.main import serve
    from rover.odometry import PoseTracker
    from tests.test_main import FakeNotifier, ScriptedInput

    clock, enc = FakeClock(), FakeEncoders()
    imu = FakeImu(rate=0.0, bias=0.05)
    pose = PoseTracker(enc, imu, calibrator=BiasCalibrator(samples=20))
    snaps = []

    class Status:
        def publish(self, s):
            snaps.append(s)

    class Input(ScriptedInput):
        def poll(self):
            if clock.now() < 1.0:
                return []  # still: the gyro calibrates
            return [DriveCommand(0.3, 0.3, "bench", clock.now())]

    def sleep(s):
        clock.advance(0.02)
        if clock.now() > 1.0:
            enc.add(1, 1)

    serve(motors, clock, FakeNotifier(), Events(io.StringIO(), clock), Input({}), ticks=100,
          sleep=sleep, status=Status(), pose=pose)
    assert imu.bias == pytest.approx(0.05)  # learned while still
    p = snaps[-1]["pose"]
    assert p["x"] > 0.3 and abs(p["heading_deg"]) < 0.01
