import RPi.GPIO as GPIO
import time


class LED:
    def __init__(self, pin, frequency):
        self.pin = pin
        self.frequency = frequency
        self.last_blink = 0
        GPIO.setup(self.pin, GPIO.OUT)

    def blink(self, current_time):
        if current_time - self.last_blink > self.frequency:
            GPIO.output(self.pin, not GPIO.input(self.pin))
            self.last_blink = current_time


# Set up GPIO
GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)
red_led = LED(4, 0.5)
yellow_led = LED(3, 0.2)
green_led = LED(2, 0.1)


def blink_red():
    GPIO.output(red_led, GPIO.HIGH)
    time.sleep(0.5)
    GPIO.output(red_led, GPIO.LOW)
    time.sleep(0.5)


try:
    while True:
        current_time = time.monotonic()
        red_led.blink(current_time)
        yellow_led.blink(current_time)
        green_led.blink(current_time)
except KeyboardInterrupt:
    print("Exiting main")
    GPIO.cleanup()
