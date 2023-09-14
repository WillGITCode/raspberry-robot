from control.xbox_controller import XboxControllerSingleton
from state.robot_state_machine import RobotStateMachine
import RPi.GPIO as GPIO
import threading


def run_state_machine(state_machine):
    while True:
        state_machine.run()


def main():
    try:
        # get xbox controller instance
        controller = XboxControllerSingleton()
        # Create an instance of the StateMachine class
        state_machine = RobotStateMachine()
        # Set the initial state of the state machine
        state_machine.set_state("idle")

        # Start the state machine thread
        state_machine_thread = threading.Thread(
            target=run_state_machine, args=(state_machine,))
        state_machine_thread.start()

        while True:
            if controller.get_property('Back'):
                # Stop the state machine thread
                state_machine.stop()
                state_machine_thread.join()
                raise SystemExit(101)

            if controller.get_property('Start'):
                # Set the next state of the state machine
                state_machine.set_next_state("idle")

            if controller.get_property('A') == 1:
                # Set the next state of the state machine
                state_machine.set_next_state("avoid_obstacles")

            if controller.get_property('Y') == 1:
                # Set the next state of the state machine
                state_machine.set_next_state("remote_control_navigation")

            # Sleep for a short time to avoid high CPU usage
            sleep(0.01)

    finally:
        print("Exiting main")
        GPIO.cleanup()


if __name__ == '__main__':
    main()
