# This is the app entry point
# Setup and state overseen here
import RPi.GPIO as GPIO
# import pygame
import time
from modules import ping
from modules import motor
from modules import controller
# Use board based pin numbering
GPIO.setmode(GPIO.BOARD)
# create window for pygame
# screen = pygame.display.set_mode([240, 160])
# create controller
gamePad = controller.XboxController()
# Motor pins
motor.initMotors([7, 11, 13, 15])
# Servo 1 pin
servo1 = 18
# Ping 1 pin
ping1 = 16

# ping test
# try:
#     while True:
#         distance = ping.GetDistance(ping1)
#         print("Distance to object is ", distance, " cm")
#         time.sleep(1)
# finally:
#     GPIO.cleanup()

# motor test
# try:
#     motor.driveForwards()
#     time.sleep(3)
#     motor.driveBackwards()
#     time.sleep(3)
#     motor.spinLeft()
#     time.sleep(2)
#     motor.spinRight()
#     time.sleep(2)
#     motor.driveStop()
#     time.sleep(5)
# finally:
#     GPIO.cleanup()

# ping/motor test
# try:
#     while True:
#         if ping.GetDistance(ping1) > 7:
#             motor.DriveForwards()
#         else:
#             motor.DriveBackwards()
#             time.sleep(1)
#             motor.SpinLeft()
#             time.sleep(.5)
# finally:
#     GPIO.cleanup()

# pygame test
# try:
#     while True:
#         for event in pygame.event.get():
#             if event.type == pygame.KEYDOWN:
#                 if event.key == ord('q'):
#                     pygame.quit()
#                 elif event.key == pygame.K_UP:
#                     print("up")
#                     GPIO.output(7, True)
#                     GPIO.output(11, False)
#                     GPIO.output(13, True)
#                     GPIO.output(15, False)
#                 elif event.key == pygame.K_DOWN:
#                     print("down")
#                     GPIO.output(7, False)
#                     GPIO.output(11, True)
#                     GPIO.output(13, False)
#                     GPIO.output(15, True)
#                 elif event.key == pygame.K_RIGHT:
#                     print("right")
#                     GPIO.output(7, True)
#                     GPIO.output(11, False)
#                     GPIO.output(13, False)
#                     GPIO.output(15, True)
#                 elif event.key == pygame.K_LEFT:
#                     print("left")
#                     GPIO.output(7, False)
#                     GPIO.output(11, True)
#                     GPIO.output(13, True)
#                     GPIO.output(15, False)
#             elif event.type == pygame.KEYUP:
#                 print("stop")
#                 GPIO.output(7, False)
#                 GPIO.output(13, False)
#                 GPIO.output(11, False)
#                 GPIO.output(15, False)
# finally:
#     GPIO.cleanup()

# Controller test
if __name__ == '__main__':
    while True:
        if (gamePad.getProperty('Back') == 1) or (gamePad.getProperty('Start') == 1) or (gamePad.getProperty('Select') == 1):
            motor.DriveStop()
            GPIO.cleanup()
            raise SystemExit(101)
        elif gamePad.getProperty('LeftJoystickY') >= 0.7:
            print("Forward")
            while gamePad.getProperty('LeftJoystickY') >= 0.7:
                motor.DriveForwards()
            motor.DriveStop()
        # elif gamePad.getProperty('LeftJoystickY') <= -0.7:
        #     print("Backward")
        #     motor.DriveForwards()
        #     time.sleep(0.2)
        # elif gamePad.getProperty('RightTrigger') >= 0.7:
        #     print("SpinRight")
        #     motor.SpinRight()
        #     time.sleep(0.2)
        # elif gamePad.getProperty('LeftTrigger') >= 0.7:
        #     print("SpinLeft")
        #     motor.SpinLeft()
        #     time.sleep(0.2)
        # else:
        #     print("Stop")
        #     motor.DriveStop()
        #     time.sleep(0.2)
