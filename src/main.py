from state.robot_state_machine import RobotStateMachine
import RPi.GPIO as GPIO


def main():
    try:
        # Create an instance of the StateMachine class
        state_machine = RobotStateMachine()

        # Set the initial state of the state machine
        state_machine.set_state("avoid_obstacles")

        while True:
            if state_machine.get_controller().get_property('Back'):
                raise SystemExit(101)

            if state_machine.get_controller().get_property('Start'):
                state_machine.set_state("idle")

            if state_machine.get_controller().get_property('A') == 1:
                state_machine.set_state("avoid_obstacles")

            if state_machine.get_controller().get_property('Y') == 1:
                state_machine.set_state("remote_control_navigation")
    finally:
        print("Exiting main")
        GPIO.cleanup()


if __name__ == '__main__':
    main()
