import os
import time
from dataclasses import dataclass

from evdev import InputDevice, ecodes, list_devices

SEARCH_EVERY_S = 1.0
DEADZONE = 0.1
STICK_MAX = 32768.0
TRIGGER_MAX = 255.0
PAD_NAMES = ("xbox 360", "x-box 360")  # the kernel names it "Microsoft X-Box 360 pad"


@dataclass(frozen=True)
class PadState:
    lx: float = 0.0
    ly: float = 0.0  # up is positive
    rx: float = 0.0
    ry: float = 0.0
    trigger: float = 0.0  # right trigger, 0..1
    back: bool = False
    start: bool = False
    lost: bool = False


LOST = PadState(lost=True)


def _stick(raw):
    v = max(-1.0, min(1.0, raw / STICK_MAX))
    return 0.0 if abs(v) < DEADZONE else v


def find_pad(names=PAD_NAMES):
    for path in list_devices():
        dev = InputDevice(path)
        if any(n in dev.name.lower() for n in names):
            os.set_blocking(dev.fd, False)
            return dev
        dev.close()
    return None


class Pad:
    """Polled once per tick, no thread. Any error or missing device gives zeros and lost=True.

    While the pad is missing, the device search (which opens every /dev/input/event*) runs at most
    once every SEARCH_EVERY_S. A device that fails is closed before it is dropped."""

    def __init__(self, finder=find_pad, clock=time.monotonic):
        self._finder = finder
        self._clock = clock
        self._next_search = float("-inf")
        self._dev = None
        self._raw = {}
        self._buttons = {}

    def poll(self):
        try:
            if self._dev is None:
                now = self._clock()
                if now < self._next_search:
                    return LOST
                self._next_search = now + SEARCH_EVERY_S
                self._dev = self._finder()
                if self._dev is None:
                    return LOST
            while (ev := self._dev.read_one()) is not None:
                if ev.type == ecodes.EV_ABS:
                    self._raw[ev.code] = ev.value
                elif ev.type == ecodes.EV_KEY:
                    self._buttons[ev.code] = ev.value != 0
        except Exception:
            self._drop()
            return LOST
        raw = self._raw.get
        return PadState(
            lx=_stick(raw(ecodes.ABS_X, 0)),
            ly=-_stick(raw(ecodes.ABS_Y, 0)),
            rx=_stick(raw(ecodes.ABS_RX, 0)),
            ry=-_stick(raw(ecodes.ABS_RY, 0)),
            trigger=max(0.0, min(1.0, raw(ecodes.ABS_RZ, 0) / TRIGGER_MAX)),
            back=self._buttons.get(ecodes.BTN_SELECT, False),
            start=self._buttons.get(ecodes.BTN_START, False),
        )

    def _drop(self):
        dev, self._dev = self._dev, None
        self._raw.clear()
        self._buttons.clear()
        close = getattr(dev, "close", None)
        if close is not None:
            try:
                close()
            except Exception:
                pass
