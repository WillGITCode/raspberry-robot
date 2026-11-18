from rover.loop import FakeClock
from rover.ping import FakePing
from rover.scanner import AHEAD_PERIOD_S, RELAX_AFTER_S, SWEEP, Scanner
from rover.servo import AHEAD, FakeServo, pulse_us


def run(scanner, clock, seconds):
    out = []
    for _ in range(int(round(seconds / 0.02))):
        out += scanner.tick(clock.now())
        clock.advance(0.02)
    return out


def test_servo_pulses_follow_the_old_formula():
    assert (pulse_us(10), pulse_us(95), pulse_us(170)) == (511, 1456, 2289)
    assert pulse_us(0) == pulse_us(10) and pulse_us(200) == pulse_us(170)  # clamped


def test_ahead_centres_once_then_pings_at_25_hz_and_relaxes():
    clock, servo = FakeClock(), FakeServo()
    ping = FakePing(clock, distance=0.8)
    s = Scanner(ping, servo)
    readings = run(s, clock, 2.0)
    assert servo.moves == [AHEAD]
    assert all(r.angle == AHEAD and r.distance == 0.8 for r in readings)
    rate = len(readings) / (2.0 - 0.5)  # the first move settles in under 0.5 s
    assert 20 <= rate <= 1 / AHEAD_PERIOD_S + 1
    assert servo.relaxed  # held still past RELAX_AFTER_S: pulses off
    assert RELAX_AFTER_S < 2.0


def test_sweep_visits_every_angle_in_order():
    clock, servo = FakeClock(), FakeServo()
    s = Scanner(FakePing(clock, distance=1.2), servo, pattern="sweep")
    readings = run(s, clock, 6.0)
    angles = [r.angle for r in readings]
    assert angles[:len(SWEEP)] == SWEEP
    assert SWEEP[0] == 10 and max(SWEEP) == 170 and len(set(SWEEP)) == 9
    assert set(s.latest) == set(SWEEP)


def test_never_moves_during_an_echo():
    clock, servo = FakeClock(), FakeServo()
    ping = FakePing(clock, distance=None)  # each ping waits the full timeout
    s = Scanner(ping, servo, pattern="sweep")
    for _ in range(100):
        s.tick(clock.now())
        if ping.busy:
            before = len(servo.moves)
            clock.advance(0.02)
            s.tick(clock.now())
            assert len(servo.moves) == before or not ping.busy
        clock.advance(0.02)


def test_a_failed_ping_never_hides_the_valid_ones_before_it():
    clock = FakeClock()
    seq = iter([0.9, 0.7] + [None] * 40)
    s = Scanner(FakePing(clock, distance=lambda: next(seq, None)), FakeServo())
    run(s, clock, 0.6)  # settle, two valid pings, then failures start
    run(s, clock, 0.06)
    assert s.latest[AHEAD].distance is None  # the newest reading failed...
    r = s.ahead(clock.now(), max_age=0.5)
    assert r is not None and r.distance == 0.7  # ...but the guard still sees 0.7
    run(s, clock, 0.8)  # only failures for 0.8 s
    assert s.ahead(clock.now(), max_age=0.5) is None  # now it is blind
    stats = s.take_stats()
    assert stats["pings"] >= 4 and stats["ping_errors"]["no_echo"] >= 2
    assert s.take_stats() == {"pings": 0, "ping_errors": {}}


def test_ahead_takes_the_nearest_of_two_echoes():
    clock = FakeClock()
    flip = iter([0.72, 0.48] * 100)
    s = Scanner(FakePing(clock, distance=lambda: next(flip)), FakeServo())
    run(s, clock, 1.0)
    assert s.ahead(clock.now(), max_age=0.5).distance == 0.48
