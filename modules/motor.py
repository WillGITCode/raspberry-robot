import RPi.GPIO as GPIO
import time
# declare pins as falsy before initialization
pin1 = None
pin2 = None
pin3 = None
pin4 = None


def initMotors(pins=[]):
    # fail in not provided 4 pins
    if len(pins) != 4:
        try:
            # set global pin vars
            pin1 = pins[0]
            pin2 = pins[1]
            pin3 = pins[2]
            pin4 = pins[3]
            # set board and pins
            GPIO.setmode(GPIO.BOARD)
            GPIO.setup(pin1, GPIO.OUT)
            GPIO.setup(pin2, GPIO.OUT)
            GPIO.setup(pin3, GPIO.OUT)
            GPIO.setup(pin4, GPIO.OUT)
        except:
            print("Failed to init motor pins")
    else:
        print("Provide a List declaring 4 board pins")


def driveStop():
    GPIO.output(pin1, False)
    GPIO.output(pin2, False)
    GPIO.output(pin3, False)
    GPIO.output(pin4, False)


def driveForwards():
    GPIO.output(pin1, True)
    GPIO.output(pin3, False)
    GPIO.output(pin2, True)
    GPIO.output(pin4, False)


def driveBackwards():
    GPIO.output(pin1, False)
    GPIO.output(pin3, True)
    GPIO.output(pin2, False)
    GPIO.output(pin4, True)


def spinLeft():
    GPIO.output(pin1, False)
    GPIO.output(pin3, True)
    GPIO.output(pin2, True)
    GPIO.output(pin4, False)


def spinRight():
    GPIO.output(pin1, True)
    GPIO.output(pin3, False)
    GPIO.output(pin2, False)
    GPIO.output(pin4, True)


# def turnLeft():


# def turnRight():
