import RPi.GPIO as GPIO
import time
# declare pins as falsy before initialization
pin1 = None
pin2 = None
pin3 = None
pin4 = None


def init_motor_pins(pins=[]):
    # fail in not provided 4 pins
    if len(pins) == 4:
        try:
            # set global pin variables
            global pin1
            global pin2
            global pin3
            global pin4
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


def drive_stop():
    try:
        GPIO.output(pin1, False)
        GPIO.output(pin2, False)
        GPIO.output(pin3, False)
        GPIO.output(pin4, False)
        time.sleep(0.0001)
    except:
        print("drive_stop failed")


def drive_forwards():
    try:
        GPIO.output(pin1, True)
        GPIO.output(pin2, False)
        GPIO.output(pin3, True)
        GPIO.output(pin4, False)
    except:
        print("drive_forwards failed")


def drive_backwards():
    try:
        GPIO.output(pin1, False)
        GPIO.output(pin2, True)
        GPIO.output(pin3, False)
        GPIO.output(pin4, True)
    except:
        print("diveBackwards failed")


def drive_left():
    try:
        GPIO.output(pin1, True)
        GPIO.output(pin2, False)
        GPIO.output(pin3, False)
        GPIO.output(pin4, False)
    except:
        print("drive_left failed")


def drive_right():
    try:
        GPIO.output(pin1, False)
        GPIO.output(pin2, False)
        GPIO.output(pin3, True)
        GPIO.output(pin4, False)
    except:
        print("drive_right failed")


def spin_left():
    try:
        GPIO.output(pin1, False)
        GPIO.output(pin3, True)
        GPIO.output(pin2, True)
        GPIO.output(pin4, False)
    except:
        print("spin_left failed")


def spin_right():
    try:
        GPIO.output(pin1, True)
        GPIO.output(pin3, False)
        GPIO.output(pin2, False)
        GPIO.output(pin4, True)
    except:
        print("spin_right failed")
