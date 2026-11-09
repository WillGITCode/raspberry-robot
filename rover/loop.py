import time

from rover.safety import SafetyFilter


class FakeClock:
    def __init__(self, t=0.0):
        self.t = t

    def now(self):
        return self.t

    def advance(self, dt):
        self.t += dt


class TickLoop:
    """One tick: read the latest command, filter it, drive or coast. Never blocks."""

    def __init__(self, motors, clock, safety=None):
        self.motors = motors
        self.clock = clock
        self.safety = safety or SafetyFilter()
        self.command = None
        self.stale = False  # last tick coasted for lack of a fresh command

    def submit(self, command):
        self.command = command

    def tick(self):
        cmd = self.safety.apply(self.command, self.clock.now())
        self.stale = cmd is None
        if cmd is None:
            self.motors.coast()
        else:
            self.motors.drive(cmd.left, cmd.right)

    def run(self, ticks, period=0.02, sleep=time.sleep):
        for _ in range(ticks):
            self.tick()
            sleep(period)
