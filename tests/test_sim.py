from rover.command import DriveCommand
from rover.sim import Sim


def test_ping_falls_driving_toward_wall(loop, clock, no_sleep):
    sim = Sim(x=1.0, y=2.5, heading=0.0)
    ranges = [sim.ping()]
    for _ in range(50):
        loop.submit(DriveCommand(0.6, 0.6, "test", clock.now()))
        loop.tick()
        sim.step(0.6, 0.6, 0.02)
        clock.advance(0.02)
        ranges.append(sim.ping())
    assert all(b < a for a, b in zip(ranges, ranges[1:]))
    assert ranges[-1] < ranges[0]


def test_service_stops_short_of_a_wall_in_the_sim(motors):
    """The whole loop (deadman, guard, ramp) against the sim: full speed at a wall stops 20 cm short."""
    import io
    import json

    from rover.events import Events
    from rover.loop import FakeClock
    from rover.main import serve
    from rover.scanner import Scanner
    from rover.servo import FakeServo
    from rover.sim import SimMotors, SimPing
    from tests.test_main import FakeNotifier, ScriptedInput

    clock, out = FakeClock(), io.StringIO()
    sim = Sim(x=1.0, y=2.5, heading=0.0, max_speed=0.5)  # wall at x = 5 m, 4 m ahead
    sim_motors, servo = SimMotors(), FakeServo()
    scanner = Scanner(SimPing(sim, servo, clock), servo)

    class FullAhead(ScriptedInput):
        def poll(self):
            return [DriveCommand(1.0, 1.0, "bench", clock.now())]

    def sleep(s):
        sim.step(sim_motors.left, sim_motors.right, 0.02)
        clock.advance(0.02)

    serve(sim_motors, clock, FakeNotifier(), Events(out, clock), FullAhead({}), ticks=1500,
          sleep=sleep, scanner=scanner)
    gap = sim.width - sim.x
    assert 0.2 <= gap <= 0.3, gap  # stopped about 24 cm short, never touched
    states = [json.loads(x)["state"] for x in out.getvalue().splitlines() if '"obstacle_limit"' in x]
    assert "clear" in states and "slow" in states and states[-1] == "stop"
