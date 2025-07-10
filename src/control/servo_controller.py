import RPi.GPIO as GPIO
from time import sleep


class ServoController:
    def __init__(self, pin):
        self.pin = pin
        GPIO.setmode(GPIO.BOARD)
        GPIO.setup(self.pin, GPIO.OUT)
        self.pwm = GPIO.PWM(self.pin, 50)
        self.pwm.start(0)

    def set_angle(self, angle):
        self.pwm.ChangeDutyCycle(2+(angle/18))
        sleep(0.6)
        self.pwm.ChangeDutyCycle(0)
