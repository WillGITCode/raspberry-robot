from control.motor_controller import MotorController
from control.servo_controller import ServoController
from sensors.ping_sensor import PingSensor
from state.avoid_obstacles import AvoidObstaclesState
from state.idle_state import IdleState
from state.remote_control_navigation import RemoteControlNavigation


class RobotStateMachine:
    def __init__(self):
        # init ping sensor
        self.forward_ping_sensor = PingSensor(16)
        # Init motor controller
        self.motor_controller = MotorController([18, 11, 13, 15], [32, 33])
        # Init servo
        self.servo = ServoController(35)
        self.states = {
            "idle": IdleState(self.motor_controller),
            "avoid_obstacles": AvoidObstaclesState(self.motor_controller, self.forward_ping_sensor, self.servo),
            "remote_control_navigation": RemoteControlNavigation(self.motor_controller),
        }
        self.current_state = "avoid_obstacles"
        self.next_state = ""

    def add_state(self, name, state):
        self.states[name] = state

    def set_state(self, name):
        print(name)
        self.current_state = self.states[name]

    def set_next_state(self, name):
        # if the name argument is in the states dictionary and the current state is not the same as the name argument
        # then set the current state to the name argument
        if name in self.states and self.current_state != self.states[name]:
            self.set_state(name)
            # reset next state to empty string
            self.next_state = ""

    def get_state(self):
        for key, value in self.states.items():
            if value == self.current_state:
                return key

    def run(self):
        if self.next_state != "":
            self.set_state(self.next_state)
        self.current_state.run()
