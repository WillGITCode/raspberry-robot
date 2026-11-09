import os
import socket
import subprocess
import sys
import time

from rover.drive_input import DEFAULT_PATH, DriveInput
from rover.events import Events
from rover.loop import TickLoop
from rover.motors import Motors

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
          period=PERIOD_S, sleep=time.sleep, commit="unknown"):
    """Run the tick loop until `ticks` ticks are done (forever if None)."""
    loop = TickLoop(motors, clock)
    events.emit("start", commit=commit)
    notifier.notify("READY=1")
    was_stale = True
    n = 0
    try:
        while ticks is None or n < ticks:
            started = clock.now()
            for item in drive_input.poll():
                if isinstance(item, Exception):
                    events.emit("fault", error=f"bad drive input: {item}")
                    continue
                loop.submit(item)
                events.emit("drive", left=item.left, right=item.right, source=item.source)
            loop.tick()
            if loop.stale and not was_stale:
                events.emit("deadman_stop")
            was_stale = loop.stale
            elapsed = clock.now() - started
            if elapsed > period:
                events.emit("tick_overrun", elapsed=elapsed, period=period)
            notifier.notify("WATCHDOG=1")
            n += 1
            sleep(max(0.0, period - elapsed))
    except Exception as e:
        events.emit("fault", error=repr(e))
        raise
    finally:
        motors.coast()
        events.emit("stop")


def main():
    clock = RealClock()
    events = Events(sys.stdout, clock)
    motors = Motors()
    drive_input = DriveInput(os.environ.get("ROVER_DRIVE_SOCKET", DEFAULT_PATH), clock)
    try:
        serve(motors, clock, SdNotifier(), events, drive_input, commit=current_commit())
    finally:
        drive_input.close()
        motors.close()


if __name__ == "__main__":
    main()
