# class Singleton:
#     __instance = None

#     def __new__(cls):
#         if cls.__instance is None:
#             cls.__instance = super().__new__(cls)
#         return cls.__instance


# s1 = Singleton()
# s2 = Singleton()

# print(s1 is s2)  # Output: True


# p = PingSensor(16)

# while True:
#     print(p.get_distance())
#     time.sleep(0.5)

import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)

GPIO.setup(35, GPIO.OUT)
servo = GPIO.PWM(35, 50)

servo.start(0)
print("Starting servo")
time.sleep(2)

print("Moving servo")
duty = 2
while duty <= 12:
    servo.ChangeDutyCycle(duty)
    time.sleep(0.5)
    duty += 1

time.sleep(2)

print("moving servo back")

servo.ChangeDutyCycle(7)
time.sleep(2)
