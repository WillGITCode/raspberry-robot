import RPi.GPIO as GPIO
from time import sleep
from modules import ping_sensor
from modules import motor_board
from modules import control_surfaces
# create controller
gamePad = control_surfaces.XboxController()
# Motor board pins
motor_board.init_motor_pins([7, 11, 13, 15])
# Ping sensor
ping1 = ping_sensor.PingSensor(16)
# Servo 1 pin
servo1 = 18


def avoid_obstacles():
    if ping1.get_distance() > 7:
        motor_board.drive_forwards()
    else:
        motor_board.drive_backwards()
        sleep(1)
        motor_board.spin_left()
        sleep(.5)


# Entry point
def main():
    try:
        while True:
            try:
                if gamePad.get_property('Start') == 1 or gamePad.get_property('Back'):
                    motor_board.drive_stop()
                    raise SystemExit(101)
                if gamePad.get_property('A') == 1:
                    sleep(.001)
                    while gamePad.get_property('A') != 1:
                        avoid_obstacles()
                elif gamePad.get_property('LeftJoystickY') >= 0.7:
                    # print("Backward")
                    while gamePad.get_property('LeftJoystickY') >= 0.7:
                        motor_board.drive_backwards()
                elif gamePad.get_property('LeftJoystickY') <= -0.7:
                    # print("Forward")
                    while gamePad.get_property('LeftJoystickY') <= -0.7:
                        motor_board.drive_forwards()
                elif gamePad.get_property('LeftJoystickX') >= 0.7:
                    # print("Left")
                    while gamePad.get_property('LeftJoystickX') >= 0.7:
                        motor_board.drive_left()
                elif gamePad.get_property('LeftJoystickX') <= -0.7:
                    # print("Right")
                    while gamePad.get_property('LeftJoystickX') <= -0.7:
                        motor_board.drive_right()
                elif gamePad.get_property('LeftTrigger') >= 0.7:
                    # print("spin_right")
                    while gamePad.get_property('LeftTrigger') >= 0.7:
                        motor_board.spin_right()
                elif gamePad.get_property('RightTrigger') >= 0.7:
                    # print("spin_left")
                    while gamePad.get_property('RightTrigger') >= 0.7:
                        motor_board.spin_left()
                else:
                    motor_board.drive_stop()
            finally:
                sleep(0.0001)
    finally:
        GPIO.cleanup()


if __name__ == '__main__':
    main()
