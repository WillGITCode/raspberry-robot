import curses

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
        elif char == curses.KEY_DOWN:
            print("down")
        elif char == curses.KEY_RIGHT:
            print("right")
        elif char == curses.KEY_LEFT:
            print("left")
        elif char == 10:
            print("stop")
        
finally:
    # Close down curses propery, turn echo back on
    curses.nocbreak()
    screen.keypad(0)
    curses.echo()
    curses.endwin()