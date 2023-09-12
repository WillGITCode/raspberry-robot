

from time import sleep


class AvoidObstaclesState:
    def __init__(self, motor_controller, ping_sensor):
        self.ping_sensor = ping_sensor
        self.motor_controller = motor_controller

    def run(self):
        if self.ping_sensor.get_distance() > 7:
            self.motor_controller.drive_forwards(0.7)
        else:
            self.motor_controller.drive_stop()
            self.motor_controller.spin_left(1)
            sleep(0.5)
