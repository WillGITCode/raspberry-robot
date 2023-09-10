import RPi.GPIO as GPIO


class MotorController:
    def __init__(self, pins=[]):
        try:
            self.pin1 = pins[0]
            self.pin2 = pins[1]
            self.pin3 = pins[2]
            self.pin4 = pins[3]
            # set board and pins
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(self.pin1, GPIO.OUT)
            GPIO.setup(self.pin2, GPIO.OUT)
            GPIO.setup(self.pin3, GPIO.OUT)
            GPIO.setup(self.pin4, GPIO.OUT)
        except:
            print("Failed to init motor pins")

    def setup_pwm(self, speed, pins=[]):
        try:
            GPIO.setup(pins[0], GPIO.OUT)
            GPIO.setup(pins[1], GPIO.OUT)
            self.speed_left = GPIO.PWM(pins[0], speed)
            self.speed_right = GPIO.PWM(pins[1], speed)
            self.speed_left.start(speed)
            self.speed_right.start(speed)
        except:
            print("Failed to setup pwm")

    def speed_from_input(self, speed):
        try:
            return abs(speed) * 100
        except:
            print("Failed to get speed from input")

    def drive_stop(self):
        try:
            GPIO.output(self.pin1, False)
            GPIO.output(self.pin2, False)
            GPIO.output(self.pin3, False)
            GPIO.output(self.pin4, False)
        except:
            print("drive_stop failed")

    def drive_forwards(self, speed=None):
        try:
            if speed is not None:
                self.speed_left.ChangeDutyCycle(self.speed_from_input(speed))
                self.speed_right.ChangeDutyCycle(self.speed_from_input(speed))
            GPIO.output(self.pin1, True)
            GPIO.output(self.pin2, False)
            GPIO.output(self.pin3, True)
            GPIO.output(self.pin4, False)
        except:
            print("drive_forwards failed")

    def drive_backwards(self, speed=None):
        try:
            if speed is not None:
                self.speed_left.ChangeDutyCycle(self.speed_from_input(speed))
                self.speed_right.ChangeDutyCycle(self.speed_from_input(speed))
            GPIO.output(self.pin1, False)
            GPIO.output(self.pin2, True)
            GPIO.output(self.pin3, False)
            GPIO.output(self.pin4, True)
        except:
            print("diveBackwards failed")

    def drive_left(self, speed=None):
        try:
            if speed is not None:
                self.speed_left.ChangeDutyCycle(self.speed_from_input(speed))
                self.speed_right.ChangeDutyCycle(self.speed_from_input(speed))
            GPIO.output(self.pin1, False)
            GPIO.output(self.pin2, False)
            GPIO.output(self.pin3, True)
            GPIO.output(self.pin4, False)
        except:
            print("drive_left failed")

    def drive_right(self, speed=None):
        try:
            if speed is not None:
                self.speed_left.ChangeDutyCycle(self.speed_from_input(speed))
                self.speed_right.ChangeDutyCycle(self.speed_from_input(speed))
            GPIO.output(self.pin1, True)
            GPIO.output(self.pin2, False)
            GPIO.output(self.pin3, False)
            GPIO.output(self.pin4, False)
        except:
            print("drive_right failed")

    def spin_left(self, speed=None):
        try:
            if speed is not None:
                self.speed_left.ChangeDutyCycle(self.speed_from_input(speed))
                self.speed_right.ChangeDutyCycle(self.speed_from_input(speed))
            GPIO.output(self.pin1, False)
            GPIO.output(self.pin3, True)
            GPIO.output(self.pin2, True)
            GPIO.output(self.pin4, False)
        except:
            print("spin_left failed")

    def spin_right(self, speed=None):
        try:
            if speed is not None:
                self.speed_left.ChangeDutyCycle(self.speed_from_input(speed))
                self.speed_right.ChangeDutyCycle(self.speed_from_input(speed))
            GPIO.output(self.pin1, True)
            GPIO.output(self.pin3, False)
            GPIO.output(self.pin2, False)
            GPIO.output(self.pin4, True)
        except:
            print("spin_right failed")
