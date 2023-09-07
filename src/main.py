from state.robot_state_machine import RobotStateMachine
import RPi.GPIO as GPIO


def main():
    try:
        # Create an instance of the StateMachine class
        state_machine = RobotStateMachine()

        # Set the initial state of the state machine
        state_machine.set_state("avoid_obstacles")

        while True:
            if controller.get_property('Start') == 1 or controller.get_property('Back'):
                state_machine.set_state("idle")

            if controller.get_property('A') == 1:
                state_machine.set_state("avoid_obstacles")

            if controller.get_property('Y') == 1:
                state_machine.set_state("remote_control_navigation")

            # Run the state machine
            state_machine.run()
    finally:
        print("Exiting main")
        GPIO.cleanup()


if __name__ == '__main__':
    main()
