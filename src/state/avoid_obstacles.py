import time


class AvoidObstaclesState:
    def __init__(self, motor_controller, ping_sensor):
        self.ping_sensor = ping_sensor
        self.motor_controller = motor_controller
        self.timer = None
        self.last_time = time.monotonic()

    def run(self):
        if self.ping_sensor.get_distance() > 7:
            self.motor_controller.drive_forwards()
            self.cancel_timer()
        else:
            self.motor_controller.drive_backwards()
            self.start_timer()

    def start_timer(self):
        if self.timer is None:
            self.timer = time.monotonic() + 1.0
            self.last_time = time.monotonic()

    def cancel_timer(self):
        if self.timer is not None:
            self.timer = None

    def on_timer(self):
        if time.monotonic() - self.last_time >= 1.0:
            self.motor_controller.spin_left()
            self.timer = None
