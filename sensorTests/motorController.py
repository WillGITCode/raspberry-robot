import pygame
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
GPIO.setup(7,GPIO.OUT)
GPIO.setup(11,GPIO.OUT)
GPIO.setup(13,GPIO.OUT)
GPIO.setup(15,GPIO.OUT)

screen = pygame.display.set_mode([240, 160])

try:
    while True:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if event.key == ord('q'):
                    pygame.quit()
                elif event.key == pygame.K_s:
                    os.system('sudo shutdown now')
                elif event.key == pygame.K_UP:
                    print("up")
                    GPIO.output(7,True)
                    GPIO.output(11,False)
                    GPIO.output(13,True)
                    GPIO.output(15,False)
                elif event.key == pygame.K_DOWN:
                    print("down")
                    GPIO.output(7,False)
                    GPIO.output(11,True)
                    GPIO.output(13,False)
                    GPIO.output(15,True)
                elif event.key == pygame.K_RIGHT:
                    print("right")
                    GPIO.output(7,True)
                    GPIO.output(11,False)
                    GPIO.output(13,False)
                    GPIO.output(15,True)
                elif event.key == pygame.K_LEFT:
                    print("left")
                    GPIO.output(7,False)
                    GPIO.output(11,True)
                    GPIO.output(13,True)
                    GPIO.output(15,False)
            elif event.type == pygame.KEYUP:
                print("stop")
                GPIO.output(7,False)
                GPIO.output(13,False)
                GPIO.output(11,False)
                GPIO.output(15,False)
finally:
    GPIO.cleanup()
