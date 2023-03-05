import RPi.GPIO as GPIO
from time import sleep, time


class PingSensor:

    def __init__(self, pin):
        self.pin = pin

    def get_distance(self):
        try:
            # set pin to write
            GPIO.setup(self.pin, GPIO.OUT)
            # no output
            GPIO.output(self.pin, 0)
            # wait
            sleep(0.000002)
            # send trigger signal
            GPIO.output(self.pin, 1)
            # wait
            sleep(0.000005)
            # stop trigger
            GPIO.output(self.pin, 0)
            # set pin to read
            GPIO.setup(self.pin, GPIO.IN)
            # response hasn't return to sensor so start timer
            while GPIO.input(self.pin) == 0:
                starttime = time()
            # response returned end timer
            while GPIO.input(self.pin) == 1:
                endtime = time()
            duration = endtime-starttime
            # Distance is defined as time/2 (there and back) * speed of sound 34000 cm/s
            distance = duration*34000/2
            return distance
        except:
            return float('inf')
