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

# import RPi.GPIO as GPIO
# import time

# GPIO.setmode(GPIO.BOARD)

# GPIO.setup(35, GPIO.OUT)
# servo = GPIO.PWM(35, 50)

# servo.start(0)
# print("Starting servo")
# time.sleep(2)

# print("Moving servo")
# duty = 2
# while duty <= 12:
#     servo.ChangeDutyCycle(duty)
#     time.sleep(0.2)
#     servo.ChangeDutyCycle(0)
#     time.sleep(0.2)
#     duty += 1

# time.sleep(2)

# print("moving servo back")

# servo.ChangeDutyCycle(7)
# time.sleep(2)

# try:
#     while True:
#         angle = float(input("enter angle: "))
#         print(angle)
#         servo.ChangeDutyCycle(2+(angle/18))
#         time.sleep(0.5)
#         servo.ChangeDutyCycle(0)

# finally:
#     servo.stop()
#     GPIO.cleanup()

import sys


x = [1, 2, 3, 4, 5, 6, 7, 8, 9, 9, 9, 9, 99, 9, 9, 9, 9, 9, 9, 9,
     9, 9, 9, 9, 9, 9, 9, 9, 99, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9, 9]

y = map(lambda i: i**2, x)

# for i in y:
#     print(i)

print(sys.getsizeof(list(y)))
print(sys.getsizeof(y))
