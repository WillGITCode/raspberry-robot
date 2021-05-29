# Import libraries
import RPi.GPIO as GPIO
import time

# Set GPIO numbering mode
GPIO.setmode(GPIO.BOARD)

# Set pin 11 as an output, and define as servo1 as PWM pin
GPIO.setup(18,GPIO.OUT)
pwm = GPIO.PWM(18,50) # pin 11 for servo1, pulse 50Hz

def ServoSweep():
    #start PWM running, but with value of 0 (pulse off)
    pwm.start(0)
    # Define variable duty
    duty = 0
    
    # Loop for duty values from 0 to 10 (0 to 180 degrees)
    while duty <= 11:
        pwm.ChangeDutyCycle(duty)
        time.sleep(0.05)
        #pwm.ChangeDutyCycle(0)
        #time.sleep(0.001)
        duty = duty + 0.2
   

    

    

#try:
    #while True:
ServoSweep()

#finally:
    #Clean things up at the end
pwm.stop()
GPIO.cleanup()