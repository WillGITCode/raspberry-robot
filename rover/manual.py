from rover.command import DriveCommand

SPEED_CAP = 0.5
BOOST_CAP = 1.0
BOOST_THRESHOLD = 0.5  # right trigger pulled past half


def manual_command(pad, now):
    cap = BOOST_CAP if pad.trigger > BOOST_THRESHOLD else SPEED_CAP
    left = pad.ly + pad.rx
    right = pad.ly - pad.rx
    scale = max(1.0, abs(left), abs(right))
    return DriveCommand(
        left=left / scale * cap,
        right=right / scale * cap,
        source="person",
        time=now,
    )
