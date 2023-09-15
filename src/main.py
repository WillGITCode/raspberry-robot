import asyncio
from control.xbox_controller import XboxControllerSingleton
from state.robot_state_machine import RobotStateMachine
import RPi.GPIO as GPIO


def main():
    try:
        # get xbox controller instance
        controller = XboxControllerSingleton()
        # Create an instance of the StateMachine class
        state_machine = RobotStateMachine()
        # Set the initial state of the state machine
        asyncio.run(state_machine.set_next_state("idle"))

        while True:
            if controller.get_property('Back'):
                raise SystemExit(101)

            if controller.get_property('Start'):
                asyncio.run(state_machine.set_next_state("idle"))

            if controller.get_property('A') == 1:
                asyncio.run(state_machine.set_next_state("avoid_obstacles"))

            if controller.get_property('Y') == 1:
                asyncio.run(state_machine.set_next_state(
                    "remote_control_navigation"))

            asyncio.run(state_machine.run())

    finally:
        print("Exiting main")
        GPIO.cleanup()


if __name__ == '__main__':
    main()
