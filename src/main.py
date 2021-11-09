import RPi.GPIO as GPIO
import time
from modules import ping
from modules import motor
from modules import controller
# create controller
gamePad = controller.XboxController()
# Motor pins
motor.init_motor_pins([7, 11, 13, 15])
# Servo 1 pin
servo1 = 18
# Ping 1 pin
ping1 = 16


def avoid_obstacles():
    if ping.get_distance(ping1) > 7:
        motor.drive_forwards()
    else:
        motor.drive_backwards()
        time.sleep(1)
        motor.spin_left()
        time.sleep(.5)


# Entry point
def main():
    try:
        while True:
            try:
                if gamePad.get_property('Start') == 1 or gamePad.get_property('Back'):
                    motor.drive_stop()
                    raise SystemExit(101)
                if gamePad.get_property('A') == 1:
                    time.sleep(.001)
                    while gamePad.get_property('A') != 1:
                        avoid_obstacles()
                elif gamePad.get_property('LeftJoystickY') >= 0.7:
                    # print("Backward")
                    while gamePad.get_property('LeftJoystickY') >= 0.7:
                        motor.drive_backwards()
                elif gamePad.get_property('LeftJoystickY') <= -0.7:
                    # print("Forward")
                    while gamePad.get_property('LeftJoystickY') <= -0.7:
                        motor.drive_forwards()
                elif gamePad.get_property('LeftJoystickX') >= 0.7:
                    # print("Left")
                    while gamePad.get_property('LeftJoystickX') >= 0.7:
                        motor.drive_left()
                elif gamePad.get_property('LeftJoystickX') <= -0.7:
                    # print("Right")
                    while gamePad.get_property('LeftJoystickX') <= -0.7:
                        motor.drive_right()
                elif gamePad.get_property('LeftTrigger') >= 0.7:
                    # print("spin_right")
                    while gamePad.get_property('LeftTrigger') >= 0.7:
                        motor.spin_right()
                elif gamePad.get_property('RightTrigger') >= 0.7:
                    # print("spin_left")
                    while gamePad.get_property('RightTrigger') >= 0.7:
                        motor.spin_left()
                else:
                    motor.drive_stop()
            finally:
                time.sleep(0.0001)
    finally:
        GPIO.cleanup()


if __name__ == '__main__':
    main()
