from rover.command import DriveCommand

DEADMAN_S = 0.3


class SafetyFilter:
    """Passes a command only while it is fresh; otherwise returns None (coast)."""

    def __init__(self, deadman_s=DEADMAN_S):
        self.deadman_s = deadman_s

    def apply(self, command, now):
        if command is None or now - command.time > self.deadman_s:
            return None
        return command
