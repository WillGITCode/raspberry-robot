import os
import socket
from dataclasses import dataclass

from rover.command import DriveCommand

DEFAULT_PATH = "/run/rover/drive.sock"
MODE_DEFAULT_S = 10.0
MODE_MAX_S = 120.0


@dataclass(frozen=True)
class ModeRequest:
    """`mode <name> [seconds]`: run a mode for the bench, ended by the service itself at the deadline."""
    name: str
    seconds: float
    source: str
    time: float


class DriveInput:
    """Unix datagram socket the bench tool feeds with "<left> <right>" or "mode <name> [seconds]"
    lines. poll() never blocks."""

    def __init__(self, path, clock, source="bench"):
        self.path, self.clock, self.source = path, clock, source
        if os.path.exists(path):
            os.unlink(path)
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.sock.setblocking(False)
        self.sock.bind(path)

    def poll(self):
        """Return the commands received since the last call; bad lines are returned as ValueError."""
        out = []
        while True:
            try:
                data = self.sock.recv(256)
            except BlockingIOError:
                return out
            try:
                words = data.decode().split()
                if words and words[0] == "mode" and len(words) in (2, 3):
                    secs = float(words[2]) if len(words) == 3 else MODE_DEFAULT_S
                    if not 0 < secs <= MODE_MAX_S:
                        raise ValueError(f"mode seconds must be in (0, {MODE_MAX_S:g}]: {secs}")
                    out.append(ModeRequest(words[1], secs, self.source, self.clock.now()))
                    continue
                left, right = (float(x) for x in words)
                out.append(DriveCommand(left, right, self.source, self.clock.now()))
            except ValueError as e:
                out.append(e)

    def close(self):
        self.sock.close()
        if os.path.exists(self.path):
            os.unlink(self.path)
