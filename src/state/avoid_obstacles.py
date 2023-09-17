

from time import sleep, time
MINIMUM_FORWARD_DISTANCE = 8
MINIMUM_SIDE_DISTANCE = 16
directions = ["left", "right", "turn_around"]


class AvoidObstaclesState:
    def __init__(self, motor_controller, ping_sensor, ping_servo):
        self.ping_sensor = ping_sensor
        self.motor_controller = motor_controller
        self.ping_servo = ping_servo
        self.last_call_time = time()

    def run(self):
        # Reset the servo to the middle
        self.ping_servo.set_angle(95)
        # Drive forwards until the distance is less than the minimum forward distance
        while self.ping_sensor.get_distance() > MINIMUM_FORWARD_DISTANCE:
            current_time = time()
            if current_time - self.last_call_time > 0.1:
                self.last_call_time = current_time
                self.motor_controller.drive_forwards(0.7)

        # Stop driving
        self.motor_controller.drive_stop()
        new_direction = self.get_optimal_direction()
        # Turn in the optimal direction
        if new_direction == directions[0]:
            current_time = time()
            if current_time - self.last_call_time > 0.5:
                self.last_call_time = current_time
                self.motor_controller.spin_left(1)
                print("left")
        elif new_direction == directions[1]:
            current_time = time()
            if current_time - self.last_call_time > 0.5:
                self.motor_controller.spin_right(1)
                print("right")
        elif new_direction == directions[2]:
            current_time = time()
            if current_time - self.last_call_time > 1:
                self.motor_controller.spin_left(1)
                print("turn around")
        else:
            current_time = time()
            if current_time - self.last_call_time > 0.5:
                self.motor_controller.spin_right(1)
                print("no direction")

    def get_optimal_direction(self):
        # look left
        self.ping_servo.set_angle(10)
        left_distance = self.ping_sensor.get_distance()
        # look right
        self.ping_servo.set_angle(170)
        right_distance = self.ping_sensor.get_distance()
        # look forward
        self.ping_servo.set_angle(95)
        # turn left if no optimal direction
        if left_distance > MINIMUM_SIDE_DISTANCE and right_distance > MINIMUM_SIDE_DISTANCE:
            return directions[0]
        # turn around if left and right are too close
        elif left_distance < MINIMUM_SIDE_DISTANCE and right_distance < MINIMUM_SIDE_DISTANCE:
            return directions[2]
        # turn left if right is too close
        elif left_distance > right_distance:
            return directions[0]
        # turn right if left is too close
        elif left_distance < right_distance:
            return directions[1]
