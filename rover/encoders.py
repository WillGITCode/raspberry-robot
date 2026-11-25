"""Wheel encoders: the two 10-slot optical sensors on the front motors, counted with gpiod edge events.

Single channel: the slots give distance and speed, not direction, so each count takes its sign from
that side's motor output. NOT WIRED YET: the pins below are the proposal in hardware/wiring.md
(BOARD 29 = GPIO 5 left, BOARD 31 = GPIO 6 right). The service starts the encoders only with
ROVER_ENCODERS=1, once Boss has wired them and confirmed the pins and the 3.3 V supply.
"""
import math
from datetime import timedelta

CHIP = "/dev/gpiochip0"
GPIOS = (5, 6)  # left, right: BOARD 29 and 31, proposed in hardware/wiring.md, not confirmed
SLOTS = 10  # measured, ticket 01
WHEEL_D_M = 0.065  # measured, ticket 02
EDGES_PER_REV = 2 * SLOTS  # both edges of every slot
M_PER_EDGE = math.pi * WHEEL_D_M / EDGES_PER_REV  # about 10.2 mm
DEBOUNCE_US = 300  # kernel debounce; at full speed an edge comes about every 10 ms
MIN_EDGE_MS = 3.0  # an edge closer than this to the last one on its side is motor noise (setting min_edge_ms)


class SpikeFilter:
    """Drops edges that follow the last kept edge on the same side too closely. Counts what it dropped."""

    def __init__(self, min_interval_s=None):
        self.min_s = MIN_EDGE_MS / 1000.0 if min_interval_s is None else min_interval_s
        self.last = [None, None]
        self.dropped = [0, 0]

    def accept(self, side, t):
        last = self.last[side]
        if last is not None and t - last < self.min_s:
            self.dropped[side] += 1
            return False
        self.last[side] = t
        return True


class GpiodEncoders:
    def __init__(self, chip=CHIP, gpios=GPIOS):
        import gpiod
        from gpiod.line import Direction, Edge

        self.gpios = tuple(gpios)
        self.filter = SpikeFilter()
        settings = gpiod.LineSettings(direction=Direction.INPUT, edge_detection=Edge.BOTH,
                                      debounce_period=timedelta(microseconds=DEBOUNCE_US))
        self.req = gpiod.request_lines(chip, consumer="rover-encoders", config={self.gpios: settings})

    def read(self):
        """Edges per side (left, right) since the last call. Never blocks."""
        counts = [0, 0]
        while self.req.wait_edge_events(0):
            for ev in self.req.read_edge_events():
                side = self.gpios.index(ev.line_offset)
                if self.filter.accept(side, ev.timestamp_ns * 1e-9):
                    counts[side] += 1
        return tuple(counts)

    def close(self):
        self.req.release()


class FakeEncoders:
    def __init__(self):
        self.pending = [0, 0]
        self.filter = SpikeFilter()

    def add_edges(self, side, times):
        """Edges at these times (seconds) on one side, through the spike filter like the real ones."""
        for t in times:
            if self.filter.accept(side, t):
                self.pending[side] += 1

    def add(self, left, right):
        self.pending[0] += left
        self.pending[1] += right

    def read(self):
        out, self.pending = tuple(self.pending), [0, 0]
        return out

    def close(self):
        pass
