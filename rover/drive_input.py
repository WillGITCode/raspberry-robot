import os
import socket

from rover.command import DriveCommand

DEFAULT_PATH = "/run/rover/drive.sock"


class DriveInput:
    """Unix datagram socket the bench tool feeds with "<left> <right>" lines. poll() never blocks."""

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
                left, right = (float(x) for x in data.decode().split())
                out.append(DriveCommand(left, right, self.source, self.clock.now()))
            except ValueError as e:
                out.append(e)

    def close(self):
        self.sock.close()
        if os.path.exists(self.path):
            os.unlink(self.path)
