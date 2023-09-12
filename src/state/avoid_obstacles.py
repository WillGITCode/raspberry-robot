from threading import Timer
from time import time


class AvoidObstaclesState:
    def __init__(self, motor_controller, ping_sensor):
        self.ping_sensor = ping_sensor
        self.motor_controller = motor_controller
        self.timer = None
        self.last_time = time()

    def run(self):
        if self.ping_sensor.get_distance() > 7:
            self.motor_controller.drive_forwards()
            self.cancel_timer()
        else:
            self.motor_controller.drive_backwards()
            self.start_timer()

    def start_timer(self):
        if self.timer is None:
            self.timer = Timer(1.0, self.on_timer)
            self.timer.start()
            self.last_time = time()

    def cancel_timer(self):
        if self.timer is not None:
            self.timer.cancel()
            self.timer = None

    def on_timer(self):
        if time() - self.last_time >= 1.0:
            self.motor_controller.spin_left()
            self.timer = None
