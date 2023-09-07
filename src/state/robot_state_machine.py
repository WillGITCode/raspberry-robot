from control.motor_controller import MotorController
from control.xbox_controller import XboxController
from sensors.ping_sensor import PingSensor
from state.avoid_obstacles import AvoidObstaclesState
from state.idle_state import IdleState
from state.remote_control_navigation import RemoteControlNavigation


class RobotStateMachine:
    def __init__(self):
        # Create an instance of the XboxController class
        self.controller = XboxController()
        # init ping sensor
        self.forward_ping_sensor = PingSensor(16)
        # Init motor controller
        self.motor_controller = MotorController()
        self.motor_controller.init_motor_pins([7, 11, 13, 15])
        self.states = {
            "idle": IdleState(self.motor_controller),
            "avoid_obstacles": AvoidObstaclesState(self.motor_controller, self.forward_ping_sensor),
            "remote_control_navigation": RemoteControlNavigation(self.motor_controller, self.controller),
        }
        self.current_state = "avoid_obstacles"

    def add_state(self, name, state):
        self.states[name] = state

    def set_state(self, name):
        self.current_state = self.states[name]

    def run(self):
        while self.current_state:
            self.current_state.run(self)
