import os
import socket
import subprocess
import sys
import time

from rover.drive_input import DEFAULT_PATH, DriveInput
from rover.events import Events
from rover.health import Health, ThrottleReader
from rover.motors import Motors
from rover.robot import Robot
from rover.scanner import Scanner

try:
    from rover.pad import Pad
except ImportError:  # python-evdev missing: run without a pad, socket input still drives
    Pad = None

PERIOD_S = 0.02


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


def serve(motors, clock, notifier, events, drive_input, ticks=None,
          period=PERIOD_S, sleep=time.sleep, commit="unknown", pad=None,
          scanner=None, health=None, status=None, pose=None):
    """Run the robot's tick at `period` until `ticks` ticks are done (forever if None): the timing,
    the systemd watchdog and the overrun check. What one tick does is rover.robot.Robot."""
    robot = Robot(motors, clock, events, drive_input, pad=pad, scanner=scanner, pose=pose,
                  status=status, health=health, commit=commit)
    events.emit("start", commit=commit)
    if robot.arbiter.manager is None:  # GH #28: say so, never run padless in silence
        why = "python-evdev missing" if Pad is None else "no pad given"
        events.emit("no_pad", reason=why, note="no Back, no Start: only the bench drives")
    notifier.notify("READY=1")
    n = 0
    try:
        while ticks is None or n < ticks:
            started = clock.now()
            robot.tick()
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
        robot.close()
        motors.coast()
        events.emit("stop")


def start_scanner(events, clock):
    """The real ping and servo, or None (with a fault event): the guard then counts as blind."""
    ping = None
    try:
        from rover.ping import GpiodPing
        from rover.servo import make_servo

        ping = GpiodPing(clock=clock.now)
        return Scanner(ping, make_servo())
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


def apply_settings(events, path=None):
    """The tunables in /etc/rover/settings.toml (or $ROVER_SETTINGS), before anything is built."""
    from rover import settings

    try:
        values = settings.load(path or os.environ.get("ROVER_SETTINGS", settings.PATH))
    except ValueError as e:
        events.emit("fault", error=str(e))
        return {}
    applied, errors = settings.apply(values)
    for error in errors:
        events.emit("fault", error=f"setting ignored: {error}")
    if applied:
        events.emit("settings", **applied)
    return applied


def main():
    clock = RealClock()
    events = Events(sys.stdout, clock)
    apply_settings(events)
    motors = Motors()
    drive_input = DriveInput(os.environ.get("ROVER_DRIVE_SOCKET", DEFAULT_PATH), clock)
    scanner = start_scanner(events, clock)
    status = start_status(events)
    pose = start_pose(events)
    if status is not None and scanner is not None and hasattr(scanner.ping, "recent"):
        status.debug["ping"] = lambda: list(scanner.ping.recent)  # copied in the server's thread
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
