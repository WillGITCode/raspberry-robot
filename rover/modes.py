from dataclasses import dataclass

from rover.idle import IdleMode
from rover.manual import manual_command
from rover.pad import PadState


@dataclass(frozen=True)
class Sense:
    """What the sensors say this tick, for modes. Modes read this; they never touch a device."""
    ahead: object = None  # the guard's reading ahead (rover.scanner.Reading) or None
    readings: tuple = ()  # the newest reading at each angle


@dataclass(frozen=True)
class Inputs:
    pad: PadState
    now: float
    sense: Sense = Sense()


def sticks_moved(pad):
    return pad.lx != 0.0 or pad.ly != 0.0 or pad.rx != 0.0  # the deadzone is already applied


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


from rover.explore import ExploreMode  # noqa: E402

REGISTRY = {"idle": IdleMode, "manual": ManualMode, "explore": ExploreMode}


class ModeManager:
    """Holds the one active mode. The stop latch outranks every mode: Back or a lost pad
    drops to idle and latches; only a fresh Start press re-arms into manual.

    Once armed: Start switches to manual, Y to explore. People beat the robot: moving a stick
    during explore takes manual control at once. A mode may ask to leave by setting `request`."""

    def __init__(self, events, registry=None):
        self.events = events
        self.registry = registry or REGISTRY
        self.name = "idle"
        self.mode = self.registry["idle"]()
        self.mode.enter()
        self.latched = True  # never starts moving by itself
        self._start_down = False
        self._y_down = False

    def switch(self, name, source):
        if name == self.name:
            return
        self.mode.exit()
        self.events.mode_change(self.name, name, source)
        self.name, self.mode = name, self.registry[name]()
        if hasattr(self.mode, "events"):
            self.mode.events = self.events
        self.mode.enter()

    def update(self, pad, now, sense=None):
        """One tick: returns the active mode's command, or None (coast)."""
        start_edge = pad.start and not self._start_down
        self._start_down = pad.start
        y_edge = pad.y and not self._y_down
        self._y_down = pad.y
        if pad.lost or pad.back:
            self.latched = True
            self.switch("idle", "pad_lost" if pad.lost else "back")
            return None
        if self.latched:
            if not start_edge:
                return None
            self.latched = False
            self.switch("manual", "start")
        elif start_edge:
            self.switch("manual", "start")
        if y_edge:
            self.switch("explore", "y")
        elif self.name == "explore" and sticks_moved(pad):
            self.switch("manual", "sticks")
        cmd = self.mode.tick(Inputs(pad, now, sense or Sense()))
        request = getattr(self.mode, "request", None)
        if request:
            self.switch(request, self.name)
            return None
        return cmd
