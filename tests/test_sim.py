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
