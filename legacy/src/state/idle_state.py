class IdleState:
    def __init__(self, motor_controller):
        self.motor_controller = motor_controller

    def run(self):
        self.motor_controller.drive_stop()
