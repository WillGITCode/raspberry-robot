# This is the app entry point
# Setup and state overseen here
import RPi.GPIO as GPIO
import time
from modules import ping
from modules import motor
# Use board based pin numbering
GPIO.setmode(GPIO.BOARD)
# Motor pins
motor.initMotors([7, 11, 13, 15])
# Servo 1 pin
servo1 = 18
# Ping 1 pin
ping1 = 16


# try:
#     while True:
#         distance = ping.GetDistance(ping1)
#         print("Distance to object is ", distance, " cm")
#         time.sleep(1)
# finally:
#     GPIO.cleanup()

try:
    motor.driveForwards()
    time.sleep(3)
    motor.driveBackwards()
    time.sleep(3)
    motor.spinLeft()
    time.sleep(2)
    motor.spinRight()
    time.sleep(2)
    motor.driveStop()
    time.sleep(5)
finally:
    GPIO.cleanup()
