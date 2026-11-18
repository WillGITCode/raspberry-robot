"""Who drives this tick. One priority rule (map ticket 09): people beat the robot, which beats agents.

1. Stop. Back or a lost pad latches idle (rover.modes.ModeManager) and ends whatever the bench was
   doing. Anyone can stop; only Start re-arms.
2. People. The pad's mode drives whenever it gives a command: manual driving, or a mode people
   started with a button, such as explore (the robot drives then, on people's say-so).
3. Agents. Today that is the bench: a bench mode or a socket drive, and only while people give no
   command and the pad is armed (Start pressed, not latched; GH #29). Voice (people) and agent control over MCP plug in here, each at its place in this order.

The arbiter only picks a command. It never touches hardware, and the safety chain in rover.loop
(deadman, obstacle guard, ramp) still filters whatever it picks.
"""
from rover.drive_input import ModeRequest

try:
    from rover.modes import REGISTRY, Inputs, Sense
    from rover.pad import PadState
except ImportError:  # python-evdev missing: no pad and no modes; socket drive still works
    REGISTRY, Inputs, Sense, PadState = {}, None, None, None


class BenchMode:
    """A mode the bench runs while no person drives, like `tools/bench drive` (stand only).

    Any pad command (people), Back, a bench drive, `mode idle`, the mode's own request or the
    deadline ends it."""

    def __init__(self, request, events):
        self.name, self.events = request.name, events
        self.deadline = request.time + request.seconds
        self.mode = REGISTRY[request.name]()
        if hasattr(self.mode, "events"):
            self.mode.events = events
        self.mode.enter()
        events.emit("bench_mode", mode=self.name, seconds=request.seconds)

    def tick(self, inputs):
        return self.mode.tick(inputs)

    def finished(self, now):
        return now >= self.deadline or bool(getattr(self.mode, "request", None))

    def end(self, reason):
        self.mode.exit()
        self.events.emit("bench_mode", mode=None, ended=self.name, reason=reason)


class Arbiter:
    def __init__(self, events, manager=None):
        self.events, self.manager = events, manager
        self.bench = None  # a BenchMode while the bench runs a mode
        self.bench_drive = None  # the last socket drive command (the deadman ages it out)
        self.last_drive = None  # (left, right, source) of the last drive event, to log changes only
        self.source = None  # who drove on the last tick: pad, bench_mode, bench_drive or None

    def receive(self, item, now):
        """One item from the drive socket: a drive command, a mode request, or a parse error."""
        if isinstance(item, Exception):
            self.events.emit("fault", error=f"bad drive input: {item}")
        elif isinstance(item, ModeRequest):
            self._end_bench("idle" if item.name == "idle" else "replaced")
            self.bench_drive = None
            if item.name == "idle":
                return
            if item.name not in REGISTRY or item.name == "manual":
                self.events.emit("fault", error=f"bench cannot run mode {item.name!r}")
                return
            self.bench = BenchMode(item, self.events)
        else:
            self._end_bench("drive")
            self.bench_drive = item
            self._note(item)

    def decide(self, now, pad_state, sense):
        """This tick's command. It may be None or stale: the deadman then coasts the motors."""
        if self.manager is not None:
            cmd = self.manager.update(pad_state, now, sense)
            if pad_state.back:
                self.bench_drive = None
            if pad_state.back or cmd is not None:
                self._end_bench("pad")
            if cmd is not None:
                self.source = "pad"
                self._note(cmd)
                return cmd
            if self.manager.latched:  # GH #29: the stop holds against the bench too; only Start re-arms
                if self.bench_drive is not None or self.bench is not None:
                    self.events.emit("bench_refused", reason="latched")
                self.bench_drive = None
                self._end_bench("latched")
                self.source = None
                return None
        if self.bench is not None:
            if self.bench.finished(now):
                self._end_bench("deadline" if now >= self.bench.deadline else "mode")
            else:
                self.source = "bench_mode"
                cmd = self.bench.tick(Inputs(pad_state or PadState(), now, sense or Sense()))
                self._note(cmd)
                return cmd
        self.source = "bench_drive" if self.bench_drive is not None else None
        self._note(self.bench_drive)
        return self.bench_drive

    def _note(self, cmd):
        """Emit a `drive` event when the command differs from the last one emitted (50 Hz stays quiet)."""
        if cmd is None:
            return
        key = (cmd.left, cmd.right, cmd.source)
        if key != self.last_drive:
            self.last_drive = key
            self.events.emit("drive", left=cmd.left, right=cmd.right, source=cmd.source)

    @property
    def active_mode(self):
        """The mode object choosing motion now (its `scan` sets the scanner's pattern)."""
        if self.bench is not None:
            return self.bench.mode
        return self.manager.mode if self.manager is not None else None

    @property
    def mode_name(self):
        if self.bench is not None:
            return f"bench:{self.bench.name}"
        return self.manager.name if self.manager is not None else None

    def close(self):
        self._end_bench("stop")

    def _end_bench(self, reason):
        if self.bench is not None:
            self.bench.end(reason)
            self.bench = None
