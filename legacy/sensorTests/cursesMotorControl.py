import curses
import RPi.GPIO as GPIO
import time

GPIO.setmode(GPIO.BOARD)
GPIO.setup(7,GPIO.OUT)
GPIO.setup(11,GPIO.OUT)
GPIO.setup(13,GPIO.OUT)
GPIO.setup(15,GPIO.OUT)

# get the curses window, turn off echoing of keyboard to screen, turn on
# instant key response, and use special values for cursor keys
screen = curses.initscr()
curses.noecho()
curses.cbreak()
screen.keypad(True)

try:
    while True:
        char = screen.getch()
        if char == ord('q'):
            break
        elif char == curses.KEY_UP:
            print("up")
            GPIO.output(7,True)
            GPIO.output(11,False)
            GPIO.output(13,True)
            GPIO.output(15,False)
        elif char == curses.KEY_DOWN:
            print("down")
            GPIO.output(7,False)
            GPIO.output(11,True)
            GPIO.output(13,False)
            GPIO.output(15,True)
        elif char == curses.KEY_RIGHT:
            print("right")
            GPIO.output(7,True)
            GPIO.output(11,False)
            GPIO.output(13,False)
            GPIO.output(15,True)
        elif char == curses.KEY_LEFT:
            print("left")
            GPIO.output(7,False)
            GPIO.output(11,True)
            GPIO.output(13,True)
            GPIO.output(15,False)
        elif char == 10:
            print("stop")
            GPIO.output(7,False)
            GPIO.output(13,False)
            GPIO.output(11,False)
            GPIO.output(15,False)
finally:
    # Close down curses propery, turn echo back on
    curses.nocbreak()
    screen.keypad(0)
    curses.echo()
    curses.endwin()
    GPIO.cleanup()