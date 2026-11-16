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


class GpiodEncoders:
    def __init__(self, chip=CHIP, gpios=GPIOS):
        import gpiod
        from gpiod.line import Direction, Edge

        self.gpios = tuple(gpios)
        settings = gpiod.LineSettings(direction=Direction.INPUT, edge_detection=Edge.BOTH,
                                      debounce_period=timedelta(microseconds=DEBOUNCE_US))
        self.req = gpiod.request_lines(chip, consumer="rover-encoders", config={self.gpios: settings})

    def read(self):
        """Edges per side (left, right) since the last call. Never blocks."""
        counts = [0, 0]
        while self.req.wait_edge_events(0):
            for ev in self.req.read_edge_events():
                counts[self.gpios.index(ev.line_offset)] += 1
        return tuple(counts)

    def close(self):
        self.req.release()


class FakeEncoders:
    def __init__(self):
        self.pending = [0, 0]

    def add(self, left, right):
        self.pending[0] += left
        self.pending[1] += right

    def read(self):
        out, self.pending = tuple(self.pending), [0, 0]
        return out

    def close(self):
        pass
