

class RemoteControlNavigation:
    def __init__(self, motor_controller, remote_controller):
        self.remote_controller = remote_controller
        self.motor_controller = motor_controller

    def run(self):
        print("Remote control navigation")
