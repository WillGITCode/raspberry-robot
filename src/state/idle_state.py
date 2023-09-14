

import threading


class IdleState:
    def __init__(self, motor_controller):
        self.motor_controller = motor_controller
        self.thread = None

    def enter(self):
        self.thread = threading.Thread(target=self.run)
        self.thread.start()

    def exit(self):
        self.thread.join()

    def run(self):
        self.motor_controller.drive_stop()
