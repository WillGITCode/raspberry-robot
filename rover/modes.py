from dataclasses import dataclass

from rover.idle import IdleMode
from rover.manual import manual_command
from rover.pad import PadState


@dataclass(frozen=True)
class Inputs:
    pad: PadState
    now: float


class Mode:
    """A mode only requests motion; it never touches hardware."""

    def enter(self):
        pass

    def tick(self, inputs):
        return None

    def exit(self):
        pass


class ManualMode(Mode):
    def tick(self, inputs):
        return manual_command(inputs.pad, inputs.now)


REGISTRY = {"idle": IdleMode, "manual": ManualMode}


class ModeManager:
    """Holds the one active mode. The stop latch outranks every mode: Back or a lost pad
    drops to idle and latches; only a fresh Start press re-arms into manual."""

    def __init__(self, events, registry=None):
        self.events = events
        self.registry = registry or REGISTRY
        self.name = "idle"
        self.mode = self.registry["idle"]()
        self.mode.enter()
        self.latched = True  # never starts moving by itself
        self._start_down = False

    def switch(self, name, source):
        if name == self.name:
            return
        self.mode.exit()
        self.events.mode_change(self.name, name, source)
        self.name, self.mode = name, self.registry[name]()
        self.mode.enter()

    def update(self, pad, now):
        """One tick: returns the active mode's command, or None (coast)."""
        start_edge = pad.start and not self._start_down
        self._start_down = pad.start
        if pad.lost or pad.back:
            self.latched = True
            self.switch("idle", "pad_lost" if pad.lost else "back")
            return None
        if self.latched:
            if not start_edge:
                return None
            self.latched = False
            self.switch("manual", "start")
        return self.mode.tick(Inputs(pad, now))
