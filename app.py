# This is the app entry point
# Setup and state overseen here
import RPi.GPIO as GPIO
# import pygame
import time
from modules import ping
from modules import motor
from modules import controller
# create controller
gamePad = controller.XboxController()
# Motor pins
motor.initMotors([7, 11, 13, 15])
# Servo 1 pin
servo1 = 18
# Ping 1 pin
ping1 = 16


def AvoidObstacles():
    if ping.GetDistance(ping1) > 7:
        motor.DriveForwards()
    else:
        motor.DriveBackwards()
        time.sleep(1)
        motor.SpinLeft()
        time.sleep(.5)


# Controller test
if __name__ == '__main__':
    try:
        while True:
            try:
                if gamePad.getProperty('Start') == 1 or gamePad.getProperty('Back'):
                    motor.DriveStop()
                    raise SystemExit(101)
                if gamePad.getProperty('A') == 1:
                    time.sleep(.001)
                    while gamePad.getProperty('A') != 1:
                        AvoidObstacles()
                elif gamePad.getProperty('LeftJoystickY') >= 0.7:
                    # print("Backward")
                    while gamePad.getProperty('LeftJoystickY') >= 0.7:
                        motor.DriveBackwards()
                elif gamePad.getProperty('LeftJoystickY') <= -0.7:
                    # print("Forward")
                    while gamePad.getProperty('LeftJoystickY') <= -0.7:
                        motor.DriveForwards()
                elif gamePad.getProperty('LeftJoystickX') >= 0.7:
                    # print("Left")
                    while gamePad.getProperty('LeftJoystickX') >= 0.7:
                        motor.DriveLeft()
                elif gamePad.getProperty('LeftJoystickX') <= -0.7:
                    # print("Right")
                    while gamePad.getProperty('LeftJoystickX') <= -0.7:
                        motor.DriveRight()
                elif gamePad.getProperty('LeftTrigger') >= 0.7:
                    # print("SpinRight")
                    while gamePad.getProperty('LeftTrigger') >= 0.7:
                        motor.SpinRight()
                elif gamePad.getProperty('RightTrigger') >= 0.7:
                    # print("SpinLeft")
                    while gamePad.getProperty('RightTrigger') >= 0.7:
                        motor.SpinLeft()
                else:
                    motor.DriveStop()
            finally:
                time.sleep(0.0001)
    finally:
        GPIO.cleanup()
