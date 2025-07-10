import RPi.GPIO as GPIO
import time


def GetDistance(pin):
    try:
        # set pin to write
        GPIO.setup(pin, GPIO.OUT)
        # no output
        GPIO.output(pin, 0)
        # wait
        time.sleep(0.000002)
        # send trigger signal
        GPIO.output(pin, 1)
        # wait
        time.sleep(0.000005)
        # stop trigger
        GPIO.output(pin, 0)
        # set pin to read
        GPIO.setup(pin, GPIO.IN)
        # response hasn't return to sensor so start timer
        while GPIO.input(pin) == 0:
            starttime = time.time()
        # response returned end timer
        while GPIO.input(pin) == 1:
            endtime = time.time()
        duration = endtime-starttime
        # Distance is defined as time/2 (there and back) * speed of sound 34000 cm/s
        distance = duration*34000/2
        return distance
    except:
        return float('inf')
