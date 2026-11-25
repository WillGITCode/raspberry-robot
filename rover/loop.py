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

    def __init__(self, motors, clock, safety=None, ramp=None, guard=None, drivetrain=None):
        self.motors = motors
        self.clock = clock
        self.safety = safety or SafetyFilter()
        self.ramp = ramp or Ramp()
        self.guard = guard
        self.drivetrain = drivetrain  # target speed -> duty (rover.drivetrain); None: duty = target
        self.command = None
        self.stale = False  # last tick coasted for lack of a fresh command
        self.output = (0.0, 0.0)  # what the motors got on the last tick (duty)
        self.target = (0.0, 0.0)  # the filtered target speeds on the last tick
        self.edges = None  # this tick's encoder counts (left, right), set by the robot; None: no encoders

    def submit(self, command):
        self.command = command

    def tick(self):
        now = self.clock.now()
        cmd = self.safety.apply(self.command, now)
        self.stale = cmd is None
        if cmd is None:
            self.ramp.reset()
            if self.drivetrain is not None:
                self.drivetrain.reset()
            self.target = self.output = (0.0, 0.0)
            self.motors.coast()
            return
        left, right = cmd.left, cmd.right
        if self.guard is not None:
            left, right = self.guard.limit(left, right, now)
        self.target = self.ramp.apply(left, right, now)
        self.output = self.target
        if self.drivetrain is not None:
            self.output = self.drivetrain.duty(now, self.target, self.edges)
            if self.drivetrain.fault is not None:  # encoder_fault: the stop outranks the command
                self.ramp.reset()
                self.motors.coast()
                return
        self.motors.drive(*self.output)

    def run(self, ticks, period=0.02, sleep=time.sleep):
        for _ in range(ticks):
            self.tick()
            sleep(period)
