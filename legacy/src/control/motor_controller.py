import RPi.GPIO as GPIO


class MotorController:

    def __init__(self, drive_pins=[], pwm_pins=[]):
        # set board and pins
        self.speed_left = None
        self.speed_right = None
        try:
            self.left_forward = drive_pins[0]
            self.left_backward = drive_pins[1]
            self.right_forward = drive_pins[2]
            self.right_backward = drive_pins[3]
            # setup GPIO
            GPIO.setmode(GPIO.BOARD)
            # setup drive pins
            GPIO.setup(self.left_forward, GPIO.OUT)
            GPIO.setup(self.left_backward, GPIO.OUT)
            GPIO.setup(self.right_forward, GPIO.OUT)
            GPIO.setup(self.right_backward, GPIO.OUT)
            # setup pwm pins
            GPIO.setup(pwm_pins[0], GPIO.OUT)
            GPIO.setup(pwm_pins[1], GPIO.OUT)
            self.speed_left = GPIO.PWM(pwm_pins[0], 100)
            self.speed_right = GPIO.PWM(pwm_pins[1], 100)
            self.speed_left.start(100)
            self.speed_right.start(100)
        except:
            print("Failed to init motor pins")

    def speed_from_input(self, speed):
        try:
            return abs(speed) * 100
        except:
            print("Failed to get speed from input")

    def drive_stop(self):
        try:
            GPIO.output(self.left_forward, False)
            GPIO.output(self.left_backward, False)
            GPIO.output(self.right_forward, False)
            GPIO.output(self.right_backward, False)
        except:
            print("drive_stop failed")

    def drive_forwards(self, speed=None):
        try:
            if speed is not None:
                self.speed_left.ChangeDutyCycle(self.speed_from_input(speed))
                self.speed_right.ChangeDutyCycle(self.speed_from_input(speed))
            GPIO.output(self.left_forward, True)
            GPIO.output(self.left_backward, False)
            GPIO.output(self.right_forward, True)
            GPIO.output(self.right_backward, False)
        except:
            print("drive_forwards failed")

    def drive_backwards(self, speed=None):
        try:
            if speed is not None:
                self.speed_left.ChangeDutyCycle(self.speed_from_input(speed))
                self.speed_right.ChangeDutyCycle(self.speed_from_input(speed))
            GPIO.output(self.left_forward, False)
            GPIO.output(self.left_backward, True)
            GPIO.output(self.right_forward, False)
            GPIO.output(self.right_backward, True)
        except:
            print("diveBackwards failed")

    def drive_left(self, speed=None):
        try:
            if speed is not None:
                self.speed_left.ChangeDutyCycle(self.speed_from_input(speed))
                self.speed_right.ChangeDutyCycle(self.speed_from_input(speed))
            GPIO.output(self.left_forward, False)
            GPIO.output(self.left_backward, False)
            GPIO.output(self.right_forward, True)
            GPIO.output(self.right_backward, False)
        except:
            print("drive_left failed")

    def drive_right(self, speed=None):
        try:
            if speed is not None:
                self.speed_left.ChangeDutyCycle(self.speed_from_input(speed))
                self.speed_right.ChangeDutyCycle(self.speed_from_input(speed))
            GPIO.output(self.left_forward, True)
            GPIO.output(self.left_backward, False)
            GPIO.output(self.right_forward, False)
            GPIO.output(self.right_backward, False)
        except:
            print("drive_right failed")

    def spin_left(self, speed=None):
        try:
            if speed is not None:
                self.speed_left.ChangeDutyCycle(self.speed_from_input(speed))
                self.speed_right.ChangeDutyCycle(self.speed_from_input(speed))
            GPIO.output(self.left_forward, False)
            GPIO.output(self.right_forward, True)
            GPIO.output(self.left_backward, True)
            GPIO.output(self.right_backward, False)
        except:
            print("spin_left failed")

    def spin_right(self, speed=None):
        try:
            if speed is not None:
                self.speed_left.ChangeDutyCycle(self.speed_from_input(speed))
                self.speed_right.ChangeDutyCycle(self.speed_from_input(speed))
            GPIO.output(self.left_forward, True)
            GPIO.output(self.right_forward, False)
            GPIO.output(self.left_backward, False)
            GPIO.output(self.right_backward, True)
        except:
            print("spin_right failed")
