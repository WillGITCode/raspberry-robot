from time import sleep


class State:
    def run(self):
        pass

    def next(self):
        pass


class AvoidObstacles(State):
    def run(self):
        # Check for obstacles and navigate around them
        print("Check for obstacles and navigate around them")
        sleep(1)
        pass

    def next(self):
        # Switch to another state if necessary
        print("Leaving AvoidObstacles")
        pass


class VoiceCommand(State):
    def run(self):
        # Listen for voice commands and respond appropriately
        print("Listen for voice commands and respond appropriately")
        sleep(1)
        pass

    def next(self):
        # Switch to another state if necessary
        print("Leaving VoiceCommand")
        pass


class MotorControl(State):
    def run(self):
        # Control the robot's motors based on input from a wireless controller
        print("Control the robot's motors based on input from a wireless controller")
        sleep(1)
        pass

    def next(self):
        # Switch to another state if necessary
        print("Leaving MotorControl")
        pass


class StateMachine:
    def __init__(self):
        self.avoid_obstacles = AvoidObstacles()
        self.voice_command = VoiceCommand()
        self.motor_control = MotorControl()
        self.state = self.avoid_obstacles

    def run(self):
        while True:
            self.state.run()
            self.state.next()

    def set_state(self, state):
        self.state = state

    def get_state(self):
        return self.state

    def change_state(self):
        # Define a mapping of user input to state objects
        state_map = {'1': self.avoid_obstacles,
                     '2': self.voice_command,
                     '3': self.motor_control}

        # Display the options to the user
        print("Select a state:")
        print("1. Avoid Obstacles")
        print("2. Voice Command")
        print("3. Motor Control")

        # Get user input and change the state accordingly
        choice = input()
        if choice in state_map:
            self.set_state(state_map[choice])
        else:
            print("Invalid choice. Please try again.")

        # Print the current state
        print("Current state:", type(self.state).__name__)


# Entry point
def main():
    try:
        state_machine = StateMachine()
        while True:
            state_machine.change_state()
            state_machine.run()
    finally:
        print("Exiting main")


if __name__ == '__main__':
    main()
