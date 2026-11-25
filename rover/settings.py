"""Tunables you can change on the robot without a deploy: /etc/rover/settings.toml.

Each setting maps to one module constant that is read when it is used, and has a safe range. At start
the service applies the file and logs a `settings` event; a bad file or value is a `fault`, and the
default stays. `tools/bench tune key=value ...` checks the values here, writes the file on the Pi and
restarts the service (about 2 s, no deploy). `python -m rover.settings --list` prints them all.
"""
import importlib
import sys
import tomllib

PATH = "/etc/rover/settings.toml"

# name: (module, constant, low, high, what it does)
TUNABLES = {
    "speed_cap": ("rover.manual", "SPEED_CAP", 0.1, 1.0, "pad speed without the trigger"),
    "boost_cap": ("rover.manual", "BOOST_CAP", 0.1, 1.0,
                  "pad speed with the right trigger (0.85: at 1.0 motor noise blinds the ping)"),
    "inner_drop": ("rover.manual", "INNER_DROP", 0.0, 2.0,
                   "steering: inner side slowdown at full sideways (0.5 half, 1.0 stopped, 1.3 back at 30%, 2.0 spin)"),
    "turn_cap": ("rover.manual", "TURN_CAP", 0.1, 1.0,
                 "steering: outer side cap at full sideways (rises from speed_cap with |lx|)"),
    "deadzone": ("rover.pad", "DEADZONE", 0.02, 0.3, "stick deadzone"),
    "accel_per_s": ("rover.ramp", "ACCEL_PER_S", 1.0, 20.0, "speed-up rate per second (4: 0 to full in 0.25 s)"),
    "guard_stop_m": ("rover.guard", "STOP_M", 0.10, 1.0, "guard: forward speed reaches 0 here"),
    "guard_slow_m": ("rover.guard", "SLOW_M", 0.2, 2.0, "guard: full forward speed from here"),
    "guard_blind_cap": ("rover.guard", "BLIND_CAP", 0.0, 0.5, "guard: forward cap with no reading"),
    "explore_speed": ("rover.explore", "CRUISE_SPEED", 0.1, 0.6, "explore: cruise speed"),
    "explore_turn_speed": ("rover.explore", "TURN_SPEED", 0.2, 0.8, "explore: spin speed"),
    "explore_look_at_m": ("rover.explore", "LOOK_AT_M", 0.25, 1.5, "explore: stop and look at this distance"),
    "explore_open_m": ("rover.explore", "OPEN_M", 0.4, 2.0, "explore: ahead counts as open from here"),
    "explore_side_m": ("rover.explore", "SIDE_M", 0.2, 1.0, "explore: veer from a side closer than this"),
    "edge_m_left": ("rover.drivetrain", "M_PER_EDGE_LEFT", 0.005, 0.02, "left wheel: metres per encoder edge (measured on the floor)"),
    "edge_m_right": ("rover.drivetrain", "M_PER_EDGE_RIGHT", 0.005, 0.02, "right wheel: metres per encoder edge"),
    "trim": ("rover.drivetrain", "TRIM", -0.2, 0.2, "open loop (no encoders): right duty x (1+trim), left x (1-trim); positive cures a drift right"),
    "min_edge_ms": ("rover.encoders", "MIN_EDGE_MS", 0.5, 10.0, "encoders: drop an edge closer than this to the last (motor noise)"),
    "max_speed_mps": ("rover.drivetrain", "MAX_SPEED_MPS", 0.2, 3.0, "speed at duty 1.0 (feed-forward scale)"),
    "pi_kp": ("rover.drivetrain", "KP", 0.0, 3.0, "speed PI: duty per m/s of error"),
    "pi_ki": ("rover.drivetrain", "KI", 0.0, 10.0, "speed PI: integral gain"),
    "pi_max_correction": ("rover.drivetrain", "MAX_CORRECTION", 0.0, 0.6, "speed PI: most duty it may add or remove"),
    "duty_max": ("rover.drivetrain", "DUTY_MAX", 0.3, 1.0, "speed PI: duty ceiling (unless commanded higher)"),
    "fault_duty": ("rover.drivetrain", "FAULT_DUTY", 0.1, 1.0, "encoder fault: a side driven at least this hard ..."),
    "fault_window_s": ("rover.drivetrain", "FAULT_WINDOW_S", 0.3, 5.0, "... with no edge for this long stops the robot"),
    "max_edge_hz": ("rover.drivetrain", "MAX_EDGE_HZ", 50.0, 400.0, "encoder fault: more edges a second than this on one side"),
    "move_max_s": ("rover.move", "MAX_S", 1.0, 60.0, "moves (drive/distance/turn): time cap"),
    "move_max_m": ("rover.move", "MAX_M", 0.1, 10.0, "moves: path length cap"),
    "move_speed": ("rover.move", "SPEED", 0.1, 0.8, "moves: default speed for distance()"),
    "move_turn_rate": ("rover.move", "TURN_RATE", 0.2, 0.8, "moves: default spin speed for turn()"),
}


def check(values):
    """(good, errors): unknown names, non-numbers, out-of-range values and inconsistent pairs."""
    good, errors = {}, []
    for name, value in values.items():
        if name not in TUNABLES:
            errors.append(f"unknown setting {name!r}")
            continue
        low, high = TUNABLES[name][2:4]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            errors.append(f"{name} must be a number, not {value!r}")
        elif not low <= value <= high:
            errors.append(f"{name}={value} is outside {low}..{high}")
        else:
            good[name] = float(value)
    stop = good.get("guard_stop_m", current("guard_stop_m"))
    slow = good.get("guard_slow_m", current("guard_slow_m"))
    if slow <= stop:
        errors.append(f"guard_slow_m ({slow}) must be above guard_stop_m ({stop})")
        good.pop("guard_slow_m", None)
        good.pop("guard_stop_m", None)
    return good, errors


def current(name):
    module, attr = TUNABLES[name][:2]
    return getattr(importlib.import_module(module), attr)


def apply(values):
    """Set the good values on their modules. Returns (applied, errors)."""
    good, errors = check(values)
    for name, value in good.items():
        module, attr = TUNABLES[name][:2]
        setattr(importlib.import_module(module), attr, value)
    return good, errors


def load(path=PATH):
    """The file's values, {} if there is none; a bad file raises ValueError."""
    try:
        with open(path, "rb") as f:
            return tomllib.load(f)
    except FileNotFoundError:
        return {}
    except (tomllib.TOMLDecodeError, OSError) as e:
        raise ValueError(f"cannot read {path}: {e}") from e


def dumps(values):
    return "".join(f"{k} = {values[k]:g}\n" for k in sorted(values))


def main(argv):
    if argv[:1] == ["--list"]:
        for name, (module, attr, low, high, what) in TUNABLES.items():
            print(f"{name:20} {current(name):<6g} {low:g}..{high:g}  {what}")
        return 0
    if argv[:1] == ["--merge"]:  # current TOML on stdin, key=value args; prints the new TOML
        values = tomllib.loads(sys.stdin.read() or "")
        for arg in argv[1:]:
            name, sep, raw = arg.partition("=")
            if not sep:
                print(f"expected key=value, got {arg!r}", file=sys.stderr)
                return 2
            try:
                values[name.strip()] = float(raw)
            except ValueError:
                print(f"{name} must be a number, not {raw!r}", file=sys.stderr)
                return 2
        good, errors = check(values)
        for e in errors:
            print(e, file=sys.stderr)
        if errors:
            return 2
        sys.stdout.write(dumps(good))
        return 0
    print("usage: python -m rover.settings --list | --merge key=value ...", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
