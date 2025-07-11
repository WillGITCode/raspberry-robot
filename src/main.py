import logging
from control.xbox_controller import XboxControllerSingleton
from state.robot_state_machine import RobotStateMachine
import RPi.GPIO as GPIO


def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(message)s',
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("robot.log", mode='a', encoding='utf-8')
        ]
    )


def handle_controller_input(controller, state_machine):
    """Process controller input and update state machine as needed."""
    if controller.get_property('Back'):
        logging.info("Back button pressed. Exiting.")
        return False  # Signal to exit main loop

    if controller.get_property('Start'):
        state_machine.set_state("idle")

    if controller.get_property('A') == 1:
        state_machine.set_state("obstacle_avoidance")

    if controller.get_property('Y') == 1:
        state_machine.set_state("remote_control_navigation")

    return True


def main():
    setup_logging()
    logging.info("===========================================")
    logging.info("Robot service starting up.")
    controller = XboxControllerSingleton()
    state_machine = RobotStateMachine()
    running = True

    try:
        while running:
            running = handle_controller_input(controller, state_machine)
            state_machine.run()
    except Exception as e:
        logging.exception("Unhandled exception in main loop: %s", e)
    finally:
        logging.info("Exiting main")
        GPIO.cleanup()


if __name__ == '__main__':
    main()
