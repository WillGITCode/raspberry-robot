"""Parallax PING))) on one pin, read with gpiod 2 edge events on kernel timestamps. Never blocks.

One measurement: drive the pin high for about 10 us, then low, then make it an input that records
both edges. The sensor waits about 750 us, then holds the pin high for 115 us to 18.5 ms, the
echo's round trip. Later ticks collect the recorded edges without waiting. No echo within
ECHO_TIMEOUT_S, a missed rise or a pulse out of range is "no reading", never "clear".

gpiozero cannot do this: DistanceSensor needs two pins, and its flip-and-time pattern has been
broken on lgpio since kernel 6.6 (gpiozero #1135).
"""
import time
from dataclasses import dataclass

CHIP = "/dev/gpiochip0"
GPIO = 23  # BOARD 16
SPEED_OF_SOUND_M_S = 343.0  # at about 20 C
TRIGGER_NS = 10_000
MIN_WIDTH_S = 100e-6  # the sensor's shortest echo is 115 us (2 cm); shorter is a glitch
MAX_WIDTH_S = 19e-3  # its longest is 18.5 ms: nothing within about 3 m
ECHO_TIMEOUT_S = 0.03


@dataclass(frozen=True)
class Echo:
    distance: float | None  # metres to the nearest echo; None when there is no reading
    time: float  # clock time the ping was triggered
    error: str | None = None  # why there is no reading
    flip_us: float | None = None  # trigger end to input ready (bench probe)


def width_to_distance(width_s):
    return width_s * SPEED_OF_SOUND_M_S / 2


def echo_from_edges(edges, trigger_ns, t, flip_us=None):
    """edges: [(rising, timestamp_ns)] in order. An Echo, or None while the echo is still due."""
    rise = None
    for rising, ts in edges:
        if ts < trigger_ns:
            continue
        if rising:
            rise = rise if rise is not None else ts
            continue
        if rise is None:
            return Echo(None, t, "missed_rise", flip_us)  # the echo began before the pin was an input
        width = (ts - rise) / 1e9
        if width < MIN_WIDTH_S:
            return Echo(None, t, "glitch", flip_us)
        if width > MAX_WIDTH_S:
            return Echo(None, t, "too_long", flip_us)
        return Echo(width_to_distance(width), t, None, flip_us)
    return None


class GpiodPing:
    """The real sensor. trigger() starts one measurement; poll() returns it once it is done."""

    def __init__(self, chip=CHIP, gpio=GPIO, clock=time.monotonic):
        import gpiod
        from gpiod.line import Clock, Direction, Edge, Value

        self._gpiod, self._value = gpiod, Value
        self.gpio, self.clock = gpio, clock
        self._input = gpiod.LineSettings(
            direction=Direction.INPUT, edge_detection=Edge.BOTH, event_clock=Clock.MONOTONIC)
        self._high = gpiod.LineSettings(direction=Direction.OUTPUT, output_value=Value.ACTIVE)
        self.req = gpiod.request_lines(chip, consumer="rover-ping", config={gpio: self._input})
        self._pending = None  # (trigger_ns, t, flip_us, edges)

    @property
    def busy(self):
        return self._pending is not None

    def trigger(self):
        """Start a measurement. False if one is running or the pin is high (never drive an echo)."""
        if self._pending is not None:
            return False
        self._drain()
        if self.req.get_value(self.gpio) == self._value.ACTIVE:
            return False
        t = self.clock()
        self.req.reconfigure_lines(config={self.gpio: self._high})
        end = time.perf_counter_ns() + TRIGGER_NS
        while time.perf_counter_ns() < end:
            pass
        self.req.set_value(self.gpio, self._value.INACTIVE)
        trigger_ns = time.monotonic_ns()
        self.req.reconfigure_lines(config={self.gpio: self._input})
        flip_us = (time.monotonic_ns() - trigger_ns) / 1000
        self._pending = (trigger_ns, t, flip_us, [])
        return True

    def poll(self):
        """A finished Echo, or None while waiting or idle. Never blocks."""
        if self._pending is None:
            return None
        trigger_ns, t, flip_us, edges = self._pending
        edges.extend(self._drain())
        echo = echo_from_edges(edges, trigger_ns, t, flip_us)
        if echo is None and time.monotonic_ns() - trigger_ns > ECHO_TIMEOUT_S * 1e9:
            echo = Echo(None, t, "no_fall" if edges else "no_echo", flip_us)
        if echo is not None:
            self._pending = None
        return echo

    def _drain(self):
        out = []
        rising = self._gpiod.EdgeEvent.Type.RISING_EDGE
        while self.req.wait_edge_events(0):
            for ev in self.req.read_edge_events():
                out.append((ev.event_type == rising, ev.timestamp_ns))
        return out

    def close(self):
        self.req.release()


class FakePing:
    """Answers each trigger after `delay` with `distance` (None means no echo). For tests and the sim."""

    def __init__(self, clock, distance=1.0, delay=0.006):
        self.clock, self.distance, self.delay = clock, distance, delay
        self._pending = None
        self.triggers = 0

    @property
    def busy(self):
        return self._pending is not None

    def trigger(self):
        if self._pending is not None:
            return False
        self.triggers += 1
        self._pending = (self.clock.now(), self.distance() if callable(self.distance) else self.distance)
        return True

    def poll(self):
        if self._pending is None:
            return None
        t, d = self._pending
        if self.clock.now() - t < (self.delay if d is not None else ECHO_TIMEOUT_S):
            return None
        self._pending = None
        return Echo(d, t, None if d is not None else "no_echo")

    def close(self):
        pass
