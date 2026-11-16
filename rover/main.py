import os
import socket
import subprocess
import sys
import time

from rover.drive_input import DEFAULT_PATH, DriveInput, ModeRequest
from rover.events import Events
from rover.guard import FRESH_S, ObstacleGuard
from rover.health import Health, ThrottleReader
from rover.loop import TickLoop
from rover.motors import Motors
from rover.scanner import Scanner

try:
    from rover.modes import REGISTRY, Inputs, ModeManager, Sense
    from rover.pad import Pad, PadState
except ImportError:  # python-evdev missing: run without a pad, socket input still drives
    ModeManager = Pad = Sense = Inputs = PadState = None
    REGISTRY = {}

PERIOD_S = 0.02
SNAPSHOT_EVERY = 5  # ticks: the status page gets 10 snapshots a second


class RealClock:
    def now(self):
        return time.monotonic()


class SdNotifier:
    """Talks to systemd over $NOTIFY_SOCKET; does nothing when run outside systemd."""

    def __init__(self, path=None):
        path = path if path is not None else os.environ.get("NOTIFY_SOCKET")
        self.sock = None
        if path:
            self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            self.sock.connect("\0" + path[1:] if path.startswith("@") else path)

    def notify(self, message):
        if self.sock:
            self.sock.send(message.encode())


def current_commit():
    if os.environ.get("ROVER_COMMIT"):
        return os.environ["ROVER_COMMIT"]
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "HEAD"], text=True, stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError):
        return "unknown"


class BenchMode:
    """A mode the bench runs while no person drives, like `tools/bench drive` (stand only).

    Any pad command (people), Back, a bench drive, `mode idle`, the mode's own request or the
    deadline ends it."""

    def __init__(self, request, events):
        self.name, self.events = request.name, events
        self.deadline = request.time + request.seconds
        self.mode = REGISTRY[request.name]()
        if hasattr(self.mode, "events"):
            self.mode.events = events
        self.mode.enter()
        events.emit("bench_mode", mode=self.name, seconds=request.seconds)

    def tick(self, inputs):
        return self.mode.tick(inputs)

    def finished(self, now):
        return now >= self.deadline or bool(getattr(self.mode, "request", None))

    def end(self, reason):
        self.mode.exit()
        self.events.emit("bench_mode", mode=None, ended=self.name, reason=reason)


def snapshot(now, commit, manager, pad_state, loop, guard, scanner, health, pose=None, bench=None):
    """What the status page shows. Built in the loop's thread; published as one new dict."""
    cmd = loop.command
    shown = bench.mode if bench is not None else (manager.mode if manager is not None else None)
    name = f"bench:{bench.name}" if bench is not None else (manager.name if manager is not None else None)
    return {
        "t": round(now, 3),
        "commit": commit,
        "mode": name,
        "mode_state": getattr(shown, "state", None),
        "latched": manager.latched if manager is not None else None,
        "pad_lost": pad_state.lost if pad_state is not None else None,
        "command": None if cmd is None else {
            "left": cmd.left, "right": cmd.right, "source": cmd.source, "age": round(now - cmd.time, 3)},
        "output": {"left": loop.output[0], "right": loop.output[1]},
        "stale": loop.stale,
        "guard": {"state": guard.state, "distance": guard.distance, "limit": guard.limit_value},
        "ranges": [] if scanner is None else [
            {"angle": r.angle, "distance": r.distance, "error": r.error, "age": round(now - r.time, 3)}
            for r in scanner.latest.values()],
        "health": health.last if health is not None else None,
        "pose": pose.odo.pose() if pose is not None else None,
    }


def serve(motors, clock, notifier, events, drive_input, ticks=None,
          period=PERIOD_S, sleep=time.sleep, commit="unknown", pad=None,
          scanner=None, health=None, status=None, pose=None):
    """Run the tick loop until `ticks` ticks are done (forever if None)."""
    guard = ObstacleGuard(scanner, events)
    loop = TickLoop(motors, clock, guard=guard)
    events.emit("start", commit=commit)
    notifier.notify("READY=1")
    manager = ModeManager(events) if pad is not None else None
    was_stale = True
    socket_cmd = None
    last_pad = None
    bench = None  # a BenchMode while the bench runs a mode
    pad_state = None
    n = 0
    try:
        while ticks is None or n < ticks:
            started = clock.now()
            now = clock.now()
            for item in drive_input.poll():
                if isinstance(item, Exception):
                    events.emit("fault", error=f"bad drive input: {item}")
                    continue
                if isinstance(item, ModeRequest):
                    if bench is not None:
                        bench.end("replaced")
                        bench = None
                    socket_cmd = None
                    if item.name == "idle":
                        continue
                    if item.name not in REGISTRY or item.name == "manual":
                        events.emit("fault", error=f"bench cannot run mode {item.name!r}")
                        continue
                    bench = BenchMode(item, events)
                    continue
                if bench is not None:
                    bench.end("drive")
                    bench = None
                socket_cmd = item
                if manager is None:
                    loop.submit(item)
                events.emit("drive", left=item.left, right=item.right, source=item.source)
            sense = None
            if scanner is not None and Sense is not None:
                sense = Sense(ahead=scanner.ahead(now, FRESH_S), readings=tuple(scanner.latest.values()))
            cmd = None
            if manager is not None:
                # a live pad mode wins; with no pad command the bench (a mode, or the socket) drives,
                # and Back always stops both
                pad_state = pad.poll()
                cmd = manager.update(pad_state, now, sense)
                if pad_state.back:
                    socket_cmd = None
                key = None if cmd is None else (cmd.left, cmd.right, cmd.source)
                if key is not None and key != last_pad:
                    events.emit("drive", left=cmd.left, right=cmd.right, source=cmd.source)
                last_pad = key
                if bench is not None and (pad_state.back or cmd is not None):
                    bench.end("pad")
                    bench = None
            if cmd is None and bench is not None:
                if bench.finished(now):
                    bench.end("deadline" if now >= bench.deadline else "mode")
                    bench = None
                else:
                    cmd = bench.tick(Inputs(pad_state or PadState(), now, sense or Sense()))
            if manager is not None or bench is not None or cmd is not None:
                loop.submit(cmd if cmd is not None else socket_cmd)
            if scanner is not None:
                try:
                    active = bench.mode if bench is not None else (manager.mode if manager is not None else None)
                    scanner.set_pattern(getattr(active, "scan", "ahead"))
                    scanner.tick(clock.now())  # before the motors, so the guard sees this tick's echo
                except Exception as e:  # degrade, don't crash: the guard goes blind and caps forward speed
                    events.emit("fault", error=f"scanner failed, guard is blind: {e!r}")
                    scanner.close()
                    scanner = guard.scanner = None
            loop.tick()
            if pose is not None:
                try:
                    pose.tick(clock.now(), loop.output)
                except Exception as e:  # odometry is never worth a crash
                    events.emit("fault", error=f"odometry failed: {e!r}")
                    pose.close()
                    pose = None
            if loop.stale and not was_stale:
                events.emit("deadman_stop")
            was_stale = loop.stale
            if status is not None and n % SNAPSHOT_EVERY == 0:
                status.publish(snapshot(clock.now(), commit, manager, pad_state, loop, guard, scanner, health, pose,
                                        bench))
            elapsed = clock.now() - started
            if elapsed > period:
                events.emit("tick_overrun", elapsed=elapsed, period=period)
            if health is not None:
                health.tick_done(elapsed)
                health.maybe_emit(clock.now())
            notifier.notify("WATCHDOG=1")
            n += 1
            sleep(max(0.0, period - elapsed))
    except Exception as e:
        events.emit("fault", error=repr(e))
        raise
    finally:
        if bench is not None:
            bench.end("stop")
        motors.coast()
        events.emit("stop")


def start_scanner(events, clock):
    """The real ping and servo, or None (with a fault event): the guard then counts as blind."""
    ping = None
    try:
        from rover.ping import GpiodPing
        from rover.servo import LgpioServo

        ping = GpiodPing(clock=clock.now)
        return Scanner(ping, LgpioServo())
    except Exception as e:
        if ping is not None:
            ping.close()
        events.emit("fault", error=f"sensors unavailable: {e!r}")
        return None


def start_pose(events):
    """Encoders and gyro, each only when its flag is set (not wired yet: hardware/wiring.md)."""
    encoders = imu = None
    if os.environ.get("ROVER_ENCODERS") == "1":
        try:
            from rover.encoders import GpiodEncoders

            encoders = GpiodEncoders()
        except Exception as e:
            events.emit("fault", error=f"encoders unavailable: {e!r}")
    if os.environ.get("ROVER_IMU") == "1":
        try:
            from rover.imu import Mpu6050

            imu = Mpu6050()
        except Exception as e:
            events.emit("fault", error=f"imu unavailable: {e!r}")
    if encoders is None and imu is None:
        return None
    from rover.odometry import PoseTracker

    return PoseTracker(encoders, imu)


def start_status(events):
    try:
        from rover.status import StatusServer

        return StatusServer(port=int(os.environ.get("ROVER_STATUS_PORT", "8080")))
    except Exception as e:
        events.emit("fault", error=f"status page unavailable: {e!r}")
        return None


def main():
    clock = RealClock()
    events = Events(sys.stdout, clock)
    motors = Motors()
    drive_input = DriveInput(os.environ.get("ROVER_DRIVE_SOCKET", DEFAULT_PATH), clock)
    scanner = start_scanner(events, clock)
    status = start_status(events)
    pose = start_pose(events)
    health = Health(events, ThrottleReader(), extras=[scanner.take_stats] if scanner is not None else [])
    try:
        serve(motors, clock, SdNotifier(), events, drive_input, commit=current_commit(),
              pad=Pad() if Pad else None, scanner=scanner, health=health, status=status, pose=pose)
    finally:
        if pose is not None:
            pose.close()
        drive_input.close()
        motors.close()
        if scanner is not None:
            scanner.close()
        if status is not None:
            status.close()


if __name__ == "__main__":
    main()
