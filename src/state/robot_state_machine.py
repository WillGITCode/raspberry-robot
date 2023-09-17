from control.motor_controller import MotorController
from control.servo_controller import ServoController
from sensors.ping_sensor import PingSensor
from state.obstacle_avoidance_state import ObstacleAvoidanceState
from state.idle_state import IdleState
from state.remote_control_state import RemoteControlState


class RobotStateMachine:
    def __init__(self):
        # init ping sensor
        self.forward_ping_sensor = PingSensor(16)
        # Init motor controller
        self.motor_controller = MotorController([18, 11, 13, 15], [32, 33])
        # Init servo
        self.servo = ServoController(5)
        self.states = {
            "idle": IdleState(self.motor_controller),
            "obstacle_avoidance": ObstacleAvoidanceState(self.motor_controller, self.forward_ping_sensor, self.servo),
            "remote_control_navigation": RemoteControlState(self.motor_controller),
        }
        self.state = self.states["idle"]

    def set_state(self, name):
        if name in self.states and self.state != self.states[name]:
            print("Changing state to: " + name)
            self.state = self.states[name]

    def run(self):
        self.state.run()
