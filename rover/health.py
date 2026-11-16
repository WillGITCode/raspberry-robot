"""Health: CPU temperature, throttle flags and tick times, as one `health` event every EVERY_S.

`vcgencmd get_throttled` takes milliseconds, so a daemon thread runs it and the tick only reads
the last value. Reading the temperature is one small sysfs read.
"""
import subprocess
import threading
import time

EVERY_S = 5.0
TEMP_PATH = "/sys/class/thermal/thermal_zone0/temp"
THROTTLE_BITS = {
    0: "under_voltage", 1: "freq_capped", 2: "throttled", 3: "soft_temp_limit",
    16: "under_voltage_seen", 17: "freq_capped_seen", 18: "throttled_seen", 19: "soft_temp_limit_seen",
}


def throttle_flags(value):
    return [name for bit, name in THROTTLE_BITS.items() if value is not None and value >> bit & 1]


def percentile(sorted_vals, q):
    if not sorted_vals:
        return None
    return sorted_vals[min(len(sorted_vals) - 1, int(q * len(sorted_vals)))]


class ThrottleReader:
    """Runs `vcgencmd get_throttled` every `every` seconds on a daemon thread."""

    def __init__(self, every=EVERY_S, cmd=("vcgencmd", "get_throttled")):
        self.value = None
        self.every, self.cmd = every, list(cmd)
        threading.Thread(target=self._run, daemon=True, name="throttle").start()

    def _run(self):
        while True:
            try:
                out = subprocess.run(self.cmd, capture_output=True, text=True, timeout=2).stdout
                self.value = int(out.strip().split("=")[1], 16)  # "throttled=0x50000"
            except Exception:
                self.value = None
            time.sleep(self.every)


class Health:
    def __init__(self, events, throttle=None, temp_path=TEMP_PATH, every=EVERY_S, extras=()):
        self.events, self.throttle, self.temp_path, self.every = events, throttle, temp_path, every
        self.extras = list(extras)  # callables returning more fields, called once per event
        self._ticks = []
        self._next = None
        self.last = None

    def tick_done(self, elapsed):
        self._ticks.append(elapsed)

    def cpu_temp(self):
        try:
            with open(self.temp_path) as f:
                return int(f.read().strip()) / 1000
        except (OSError, ValueError):
            return None

    def maybe_emit(self, now, **extra):
        if self._next is None:
            self._next = now + self.every
            return None
        if now < self._next:
            return None
        self._next = now + self.every
        ticks, self._ticks = sorted(self._ticks), []
        value = self.throttle.value if self.throttle is not None else None
        ms = lambda v: None if v is None else round(v * 1000, 2)  # noqa: E731
        self.last = {
            "cpu_temp": self.cpu_temp(),
            "throttled": None if value is None else hex(value),
            "throttle_flags": throttle_flags(value),
            "ticks": len(ticks),
            "tick_ms_p50": ms(percentile(ticks, 0.5)),
            "tick_ms_p99": ms(percentile(ticks, 0.99)),
            "tick_ms_max": ms(ticks[-1] if ticks else None),
            **extra,
        }
        for fn in self.extras:
            self.last.update(fn())
        self.events.emit("health", **self.last)
        return self.last
