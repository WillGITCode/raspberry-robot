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
        state = gamePad.getState()
        if state[4] == 1 or state[5]:
            motor.DriveStop()
            motor.MotorShutDown()
            raise SystemExit(101)
        elif state[0] >= 0.7:
            # print("Backward")
            while state[0] >= 0.7:
                motor.DriveBackwards()
            motor.DriveStop()
        elif state[0] <= -0.7:
            # print("Forward")
            while state[0] <= -0.7:
                motor.DriveForwards()
            motor.DriveStop()
        elif state[1] >= 0.7:
            # print("Left")
            while state[1] >= 0.7:
                motor.DriveLeft()
            motor.DriveStop()
        elif state[1] <= -0.7:
            # print("Right")
            while state[1] <= -0.7:
                motor.DriveRight()
            motor.DriveStop()
        elif state[2] >= 0.7:
            # print("SpinRight")
            while state[2] >= 0.7:
                motor.SpinRight()
            motor.DriveStop()
        elif state[3] >= 0.7:
            # print("SpinLeft")
            while state[3] >= 0.7:
                motor.SpinLeft()
            motor.DriveStop()
