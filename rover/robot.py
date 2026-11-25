"""One tick of the robot, in this order:

    inputs (drive socket, pad) -> arbiter (who drives) -> sensors (scanner) ->
    safety chain and motors (rover.loop: deadman, guard, ramp) -> odometry -> telemetry

Each stage is one component with a fake for tests. A failing sensor or odometry degrades with a
`fault` event instead of stopping the robot's loop; the guard then counts as blind.
"""
from rover.control import Arbiter
from rover.drivetrain import Drivetrain
from rover.guard import FRESH_S, ObstacleGuard
from rover.loop import TickLoop

try:
    from rover.modes import ModeManager, Sense
except ImportError:  # python-evdev missing
    ModeManager = Sense = None

SNAPSHOT_EVERY = 5  # ticks: the status page gets 10 snapshots a second
RECENT_S = 1.0  # modes count as blind only after this long with no valid reading ahead


class Robot:
    def __init__(self, motors, clock, events, drive_input, pad=None, scanner=None, pose=None,
                 status=None, health=None, commit="unknown"):
        self.clock, self.events, self.drive_input, self.pad = clock, events, drive_input, pad
        self.scanner, self.pose, self.status, self.health, self.commit = scanner, pose, status, health, commit
        self.guard = ObstacleGuard(scanner, events)
        self.drivetrain = Drivetrain(events, closed_loop=pose is not None and getattr(pose, "encoders", None) is not None)
        self.loop = TickLoop(motors, clock, guard=self.guard, drivetrain=self.drivetrain)
        manager = ModeManager(events) if pad is not None and ModeManager is not None else None
        self.arbiter = Arbiter(events, manager)
        self.pad_state = None
        self._was_stale = True
        self._fault_seen = False
        self.n = 0

    def tick(self):
        now = self.clock.now()
        for item in self.drive_input.poll():
            self.arbiter.receive(item, now)
        self.pad_state = self.pad.poll() if self.pad is not None else None
        self._read_encoders()  # first: the kernel buffer is small
        odo = self.pose.odo if self.pose is not None else None
        self.loop.submit(self.arbiter.decide(now, self.pad_state, self.sense(now), odo))
        self._scan()  # before the motors, so the guard sees this tick's echo
        self.loop.tick()
        self._odometry()
        self._encoder_fault()
        if self.loop.stale and not self._was_stale:
            self.events.emit("deadman_stop")
        self._was_stale = self.loop.stale
        if self.status is not None and self.n % SNAPSHOT_EVERY == 0:
            self.status.publish(self.snapshot(self.clock.now()))
        self.n += 1

    def sense(self, now):
        if self.scanner is None or Sense is None:
            return None
        return Sense(ahead=self.scanner.ahead(now, FRESH_S), readings=tuple(self.scanner.latest.values()),
                     ahead_recent=self.scanner.ahead(now, RECENT_S))

    def _scan(self):
        if self.scanner is None:
            return
        try:
            self.scanner.set_pattern(getattr(self.arbiter.active_mode, "scan", "ahead"))
            self.scanner.tick(self.clock.now())
        except Exception as e:  # degrade, don't crash: the guard goes blind and caps forward speed
            self.events.emit("fault", error=f"scanner failed, guard is blind: {e!r}")
            self.scanner.close()
            self.scanner = self.guard.scanner = None

    def _read_encoders(self):
        self.loop.edges = None
        if self.pose is None:
            return
        try:
            self.loop.edges = self.pose.read()
        except Exception as e:  # no edges: open loop from here on
            self.events.emit("fault", error=f"encoders failed, open loop: {e!r}")
            self.drivetrain.closed_loop = False
            self.pose.encoders = None

    def _encoder_fault(self):
        """The encoder_fault stop is latched like the pad's: Start re-arms it (no pad: restart the service)."""
        manager = self.arbiter.manager
        if self.drivetrain.fault is None:
            return
        if manager is None:
            return
        if not self._fault_seen:
            self._fault_seen = True
            manager.latched = True
            manager.switch("idle", "encoder_fault")
        elif not manager.latched:  # Start pressed after the fault
            self.drivetrain.rearm()
            self._fault_seen = False

    def _odometry(self):
        if self.pose is None:
            return
        try:
            self.pose.tick(self.clock.now(), self.loop.output)
        except Exception as e:  # odometry is never worth a crash
            self.events.emit("fault", error=f"odometry failed: {e!r}")
            self.pose.close()
            self.pose = None

    def snapshot(self, now):
        """What the status page shows. Built in the loop's thread; published as one new dict."""
        cmd, manager = self.loop.command, self.arbiter.manager
        return {
            "t": round(now, 3),
            "commit": self.commit,
            "mode": self.arbiter.mode_name,
            "mode_state": getattr(self.arbiter.active_mode, "state", None),
            "driver": self.arbiter.source,
            "latched": manager.latched if manager is not None else None,
            "pad_lost": self.pad_state.lost if self.pad_state is not None else None,
            "command": None if cmd is None else {
                "left": cmd.left, "right": cmd.right, "source": cmd.source, "age": round(now - cmd.time, 3)},
            "output": {"left": self.loop.output[0], "right": self.loop.output[1]},
            "target": {"left": self.loop.target[0], "right": self.loop.target[1]},
            "wheel_speed": list(self.drivetrain.speed),
            "encoder_fault": self.drivetrain.fault,
            "stale": self.loop.stale,
            "guard": {"state": self.guard.state, "distance": self.guard.distance, "limit": self.guard.limit_value},
            "ranges": [] if self.scanner is None else [
                {"angle": r.angle, "distance": r.distance, "error": r.error, "age": round(now - r.time, 3)}
                for r in self.scanner.latest.values()],
            "health": self.health.last if self.health is not None else None,
            "pose": self.pose.odo.pose() if self.pose is not None else None,
        }

    def close(self):
        self.arbiter.close()
