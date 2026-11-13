from evdev import ecodes

from rover.pad import Pad


class Ev:
    def __init__(self, type, code, value):
        self.type, self.code, self.value = type, code, value


class FakeDev:
    def __init__(self):
        self.events = []
        self.gone = False

    def read_one(self):
        if self.gone:
            raise OSError("device removed")
        return self.events.pop(0) if self.events else None


def abs_ev(code, value):
    return Ev(ecodes.EV_ABS, code, value)


def test_stick_normalised_and_inverted():
    dev = FakeDev()
    dev.events = [abs_ev(ecodes.ABS_Y, -32768), abs_ev(ecodes.ABS_RX, 16384)]
    s = Pad(lambda: dev).poll()
    assert s.ly == 1.0 and s.rx == 0.5 and not s.lost


def test_deadzone_gives_zero():
    dev = FakeDev()
    dev.events = [abs_ev(ecodes.ABS_Y, 3000), abs_ev(ecodes.ABS_X, -3000)]
    s = Pad(lambda: dev).poll()
    assert s.ly == 0.0 and s.lx == 0.0


def test_buttons_and_trigger():
    dev = FakeDev()
    dev.events = [
        Ev(ecodes.EV_KEY, ecodes.BTN_START, 1),
        abs_ev(ecodes.ABS_RZ, 255),
    ]
    s = Pad(lambda: dev).poll()
    assert s.start and not s.back and s.trigger == 1.0


def test_missing_device_is_lost():
    s = Pad(lambda: None).poll()
    assert s.lost and s.ly == 0.0


def test_removed_device_zeroes_and_lost():
    dev = FakeDev()
    dev.events = [abs_ev(ecodes.ABS_Y, -32768)]
    pad = Pad(lambda: dev)
    assert pad.poll().ly == 1.0
    dev.gone = True
    s = pad.poll()
    assert s.lost and s.ly == 0.0
