import time

from rover.ramp import Ramp
from rover.safety import SafetyFilter


class FakeClock:
    def __init__(self, t=0.0):
        self.t = t

    def now(self):
        return self.t

    def advance(self, dt):
        self.t += dt


class TickLoop:
    """One tick: read the latest command, filter it (deadman, then the obstacle guard), ramp it,
    drive or coast. Never blocks. This is the only code that moves the motors."""

    def __init__(self, motors, clock, safety=None, ramp=None, guard=None):
        self.motors = motors
        self.clock = clock
        self.safety = safety or SafetyFilter()
        self.ramp = ramp or Ramp()
        self.guard = guard
        self.command = None
        self.stale = False  # last tick coasted for lack of a fresh command
        self.output = (0.0, 0.0)  # what the motors got on the last tick

    def submit(self, command):
        self.command = command

    def tick(self):
        now = self.clock.now()
        cmd = self.safety.apply(self.command, now)
        self.stale = cmd is None
        if cmd is None:
            self.ramp.reset()
            self.output = (0.0, 0.0)
            self.motors.coast()
            return
        left, right = cmd.left, cmd.right
        if self.guard is not None:
            left, right = self.guard.limit(left, right, now)
        self.output = self.ramp.apply(left, right, now)
        self.motors.drive(*self.output)

    def run(self, ticks, period=0.02, sleep=time.sleep):
        for _ in range(ticks):
            self.tick()
            sleep(period)
