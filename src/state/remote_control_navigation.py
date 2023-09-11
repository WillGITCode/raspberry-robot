from time import sleep


class RemoteControlNavigation:
    def __init__(self, motor_controller, remote_controller):
        self.remote_controller = remote_controller
        self.motor_controller = motor_controller

    def run(self):
        print("Remote control navigation")
        try:
            if self.remote_controller.get_property('LeftJoystickY') >= 0.1:
                print("Backward")
                while self.remote_controller.get_property('LeftJoystickY') >= 0.1:
                    self.motor_controller.drive_backwards(
                        self.remote_controller.get_property('LeftJoystickY'))
            elif self.remote_controller.get_property('LeftJoystickY') <= -0.1:
                print("Forward")
                while self.remote_controller.get_property('LeftJoystickY') <= -0.1:
                    self.motor_controller.drive_forwards(
                        self.remote_controller.get_property('LeftJoystickY'))
            elif self.remote_controller.get_property('LeftJoystickX') >= 0.1:
                print("Right")
                while self.remote_controller.get_property('LeftJoystickX') >= 0.1:
                    self.motor_controller.drive_right(
                        self.remote_controller.get_property('LeftJoystickX'))
            elif self.remote_controller.get_property('LeftJoystickX') <= -0.1:
                print("Left")
                while self.remote_controller.get_property('LeftJoystickX') <= -0.1:
                    self.motor_controller.drive_left(
                        self.remote_controller.get_property('LeftJoystickX'))
            elif self.remote_controller.get_property('LeftTrigger') >= 0.1:
                print("spin_left")
                while self.remote_controller.get_property('LeftTrigger') >= 0.1:
                    self.motor_controller.spin_left(
                        self.remote_controller.get_property('LeftTrigger'))
            elif self.remote_controller.get_property('RightTrigger') >= 0.1:
                print("spin_right")
                while self.remote_controller.get_property('RightTrigger') >= 0.1:
                    self.motor_controller.spin_right(
                        self.remote_controller.get_property('RightTrigger'))
            else:
                self.motor_controller.drive_stop()
        finally:
            sleep(0.0001)
