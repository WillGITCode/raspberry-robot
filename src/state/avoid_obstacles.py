

from time import sleep
MINIMUM_DISTANCE = 7
directions = ["left", "right", "turn_around"]


class AvoidObstaclesState:
    def __init__(self, motor_controller, ping_sensor):
        self.ping_sensor = ping_sensor
        self.motor_controller = motor_controller

    def run(self):
        if self.ping_sensor.get_distance() > MINIMUM_DISTANCE:
            self.motor_controller.drive_forwards(0.7)
        else:
            self.motor_controller.drive_stop()
            self.motor_controller.spin_left(1)
            sleep(0.5)

    def get_optimal_direction(self):
        left_distance
        right_distance
        self.ping_servo.look_left()
        # delay ?
        left_distance = self.ping_sensor.get_distance()
        self.ping_servo.look_right()
        # delay ?
        right_distance = self.ping_sensor.get_distance()
        # turn left if no optimal direction
        if left_distance > MINIMUM_DISTANCE and right_distance > MINIMUM_DISTANCE:
            return directions[0]
        # turn around if left and right are too close
        elif left_distance < MINIMUM_DISTANCE and right_distance < MINIMUM_DISTANCE:
            return directions[2]
        # turn left if right is too close
        elif left_distance > right_distance:
            return directions[0]
        # turn right if left is too close
        elif left_distance < right_distance:
            return directions[1]
