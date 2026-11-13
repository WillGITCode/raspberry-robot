import json


class Events:
    """One JSON object per line on a stream (the service's stdout, kept by journald)."""

    def __init__(self, stream, clock):
        self.stream = stream
        self.clock = clock

    def emit(self, event, **fields):
        self.stream.write(json.dumps({"t": self.clock.now(), "event": event, **fields}) + "\n")
        self.stream.flush()
