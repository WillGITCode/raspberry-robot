import RPi.GPIO as GPIO


class MotorController:
    def __init__(self):
        self.pin1 = None
        self.pin2 = None
        self.pin3 = None
        self.pin4 = None

    def init_motor_pins(self, pins=[]):
        # fail if not provided 4 pins
        if len(pins) == 4:
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
        else:
            print("Provide a List declaring 4 board pins")

    def drive_stop(self):
        try:
            GPIO.output(self.pin1, False)
            GPIO.output(self.pin2, False)
            GPIO.output(self.pin3, False)
            GPIO.output(self.pin4, False)
        except:
            print("drive_stop failed")

    def drive_forwards(self):
        try:
            GPIO.output(self.pin1, True)
            GPIO.output(self.pin2, False)
            GPIO.output(self.pin3, True)
            GPIO.output(self.pin4, False)
        except:
            print("drive_forwards failed")

    def drive_backwards(self):
        try:
            GPIO.output(self.pin1, False)
            GPIO.output(self.pin2, True)
            GPIO.output(self.pin3, False)
            GPIO.output(self.pin4, True)
        except:
            print("diveBackwards failed")

    def drive_left(self):
        try:
            GPIO.output(self.pin1, False)
            GPIO.output(self.pin2, False)
            GPIO.output(self.pin3, True)
            GPIO.output(self.pin4, False)
        except:
            print("drive_left failed")

    def drive_right(self):
        try:
            GPIO.output(self.pin1, True)
            GPIO.output(self.pin2, False)
            GPIO.output(self.pin3, False)
            GPIO.output(self.pin4, False)
        except:
            print("drive_right failed")

    def spin_left(self):
        try:
            GPIO.output(self.pin1, False)
            GPIO.output(self.pin3, True)
            GPIO.output(self.pin2, True)
            GPIO.output(self.pin4, False)
        except:
            print("spin_left failed")

    def spin_right(self):
        try:
            GPIO.output(self.pin1, True)
            GPIO.output(self.pin3, False)
            GPIO.output(self.pin2, False)
            GPIO.output(self.pin4, True)
        except:
            print("spin_right failed")
