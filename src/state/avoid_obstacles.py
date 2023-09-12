from time import sleep


class AvoidObstaclesState:
    def __init__(self, motor_controller, ping_sensor):
        self.ping_sensor = ping_sensor
        self.motor_controller = motor_controller
        

    def run(self):
        if self.ping_sensor.get_distance() > 7:
            self.motor_controller.drive_forwards()
        else:
            self.motor_controller.drive_backwards()
            sleep(1)
            self.motor_controller.spin_left()
