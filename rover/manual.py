from rover.command import DriveCommand

SPEED_CAP = 0.6  # Boss, 2026-11-16, after the floor runs: the gearing is low, faster is safe
BOOST_CAP = 1.0
BOOST_THRESHOLD = 0.5  # right trigger pulled past half
INNER_DROP = 0.7  # left stick fully sideways: the inner side runs at 30% of the outer (Boss: sharper)


def car_mix(ly, lx):
    """Left stick, car-like. The outer side gets the throttle; the inner side slows with |lx|.

    Pushed sideways alone, the stick arcs forward (the old code drove one side for this) and blends
    smoothly into the throttle. Pulled back, only ly sets the reverse speed, so a sideways push that
    drifts down never turns into fast reverse. Reverse arcs like a car backing up."""
    t = ly if ly < 0 else max(ly, abs(lx))
    inner = t * (1.0 - INNER_DROP * abs(lx))
    if lx < 0:  # turning left: the left side is inner
        return inner, t
    return t, inner


def manual_command(pad, now):
    """Left stick drives like a car, right stick X spins in place, right trigger boosts."""
    cap = BOOST_CAP if pad.trigger > BOOST_THRESHOLD else SPEED_CAP
    left, right = car_mix(pad.ly, pad.lx)
    left, right = left + pad.rx, right - pad.rx
    scale = max(1.0, abs(left), abs(right))
    return DriveCommand(
        left=left / scale * cap,
        right=right / scale * cap,
        source="person",
        time=now,
    )
