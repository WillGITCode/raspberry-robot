from time import sleep


class RemoteControlNavigation:
    def __init__(self, motor_controller, remote_controller):
        self.remote_controller = remote_controller
        self.motor_controller = motor_controller

    def run(self):
        print("Remote control navigation")
        while True:
            try:
                if self.remote_controller.get_property('LeftJoystickY') >= 0.7:
                    print("Backward")
                    while self.remote_controller.get_property('LeftJoystickY') >= 0.7:
                        self.motor_controller.drive_backwards()
                elif self.remote_controller.get_property('LeftJoystickY') <= -0.7:
                    print("Forward")
                    while self.remote_controller.get_property('LeftJoystickY') <= -0.7:
                        self.motor_controller.drive_forwards()
                elif self.remote_controller.get_property('LeftJoystickX') >= 0.7:
                    print("Left")
                    while self.remote_controller.get_property('LeftJoystickX') >= 0.7:
                        self.motor_controller.drive_left()
                elif self.remote_controller.get_property('LeftJoystickX') <= -0.7:
                    print("Right")
                    while self.remote_controller.get_property('LeftJoystickX') <= -0.7:
                        self.motor_controller.drive_right()
                elif self.remote_controller.get_property('LeftTrigger') >= 0.7:
                    print("spin_right")
                    while self.remote_controller.get_property('LeftTrigger') >= 0.7:
                        self.motor_controller.spin_right()
                elif self.remote_controller.get_property('RightTrigger') >= 0.7:
                    print("spin_left")
                    while self.remote_controller.get_property('RightTrigger') >= 0.7:
                        self.motor_controller.spin_left()
                else:
                    self.motor_controller.drive_stop()
            finally:
                sleep(0.0001)
