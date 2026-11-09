import os

from rover.motors import Motors


def stop(motors=None):
    """Coast: every enable and direction pin low."""
    (motors or Motors()).coast()


def main():
    stop()
    # Skip gpiozero's exit cleanup, which would release the pins and let them float.
    os._exit(0)


if __name__ == "__main__":
    main()
