from control.xbox_controller import XboxControllerSingleton
from state.robot_state_machine import RobotStateMachine
import RPi.GPIO as GPIO


def main():
    try:
        # get xbox controller instance
        controller = XboxControllerSingleton()
        # Create an instance of the StateMachine class
        state_machine = RobotStateMachine()

        while True:
            if controller.get_property('Back'):
                raise SystemExit(101)

            if controller.get_property('Start'):
                state_machine.set_state("idle")

            if controller.get_property('A') == 1:
                state_machine.set_state("obstacle_avoidance")

            if controller.get_property('Y') == 1:
                state_machine.set_state(
                    "remote_control_navigation")

            state_machine.run()

    finally:
        print("Exiting main")
        GPIO.cleanup()


if __name__ == '__main__':
    main()
