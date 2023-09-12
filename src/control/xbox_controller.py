from threading import Thread
from math import pow
from inputs import get_gamepad


class XboxControllerSingleton(object):
    MAX_TRIG_VAL = pow(2, 8)
    MAX_JOY_VAL = pow(2, 15)
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self.LeftJoystickY = 0
        self.LeftJoystickX = 0
        self.RightJoystickY = 0
        self.RightJoystickX = 0
        self.LeftTrigger = 0
        self.RightTrigger = 0
        self.LeftBumper = 0
        self.RightBumper = 0
        self.A = 0
        self.X = 0
        self.Y = 0
        self.B = 0
        self.LeftThumb = 0
        self.RightThumb = 0
        self.Back = 0
        self.Start = 0
        self.LeftDPad = 0
        self.RightDPad = 0
        self.UpDPad = 0
        self.DownDPad = 0

        self._monitor_thread = Thread(
            target=self._monitor_controller, args=())
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def get_state(self):
        return [self.LeftJoystickY,
                self.LeftJoystickX,
                self.LeftTrigger,
                self.RightTrigger,
                self.Start,
                self.Back,
                self.A]

    def get_property(self, property):
        if not isinstance(property, str):
            raise TypeError('Expected a string')
        if hasattr(self, property):
            return getattr(self, property)

    def _monitor_controller(self):
        while True:
            events = get_gamepad()
            if events is not None:
                for event in events:
                    if event.code == 'ABS_Y':
                        self.LeftJoystickY = event.state / \
                            XboxControllerSingleton.MAX_JOY_VAL  # normalize between -1 and 1
                    elif event.code == 'ABS_X':
                        self.LeftJoystickX = event.state / \
                            XboxControllerSingleton.MAX_JOY_VAL  # normalize between -1 and 1
                    elif event.code == 'ABS_RY':
                        self.RightJoystickY = event.state / \
                            XboxControllerSingleton.MAX_JOY_VAL  # normalize between -1 and 1
                    elif event.code == 'ABS_RX':
                        self.RightJoystickX = event.state / \
                            XboxControllerSingleton.MAX_JOY_VAL  # normalize between -1 and 1
                    elif event.code == 'ABS_Z':
                        self.LeftTrigger = event.state / \
                            XboxControllerSingleton.MAX_TRIG_VAL  # normalize between 0 and 1
                    elif event.code == 'ABS_RZ':
                        self.RightTrigger = event.state / \
                            XboxControllerSingleton.MAX_TRIG_VAL  # normalize between 0 and 1
                    elif event.code == 'BTN_TL':
                        self.LeftBumper = event.state
                    elif event.code == 'BTN_TR':
                        self.RightBumper = event.state
                    elif event.code == 'BTN_SOUTH':
                        self.A = event.state
                    elif event.code == 'BTN_NORTH':
                        self.X = event.state
                    elif event.code == 'BTN_WEST':
                        self.Y = event.state
                    elif event.code == 'BTN_EAST':
                        self.B = event.state
                    elif event.code == 'BTN_THUMBL':
                        self.LeftThumb = event.state
                    elif event.code == 'BTN_THUMBR':
                        self.RightThumb = event.state
                    elif event.code == 'BTN_SELECT':
                        self.Back = event.state
                    elif event.code == 'BTN_START':
                        self.Start = event.state
                    elif event.code == 'BTN_TRIGGER_HAPPY1':
                        self.LeftDPad = event.state
                    elif event.code == 'BTN_TRIGGER_HAPPY2':
                        self.RightDPad = event.state
                    elif event.code == 'BTN_TRIGGER_HAPPY3':
                        self.UpDPad = event.state
                    elif event.code == 'BTN_TRIGGER_HAPPY4':
                        self.DownDPad = event.state
