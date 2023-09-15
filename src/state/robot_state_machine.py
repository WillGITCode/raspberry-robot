import asyncio
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
        self.servo = ServoController(5)
        self.states = {
            "idle": IdleState(self.motor_controller),
            "avoid_obstacles": AvoidObstaclesState(self.motor_controller, self.forward_ping_sensor, self.servo),
            "remote_control_navigation": RemoteControlNavigation(self.motor_controller),
        }
        self.current_state = None
        self.current_state_task = None

    async def set_next_state(self, name):
        if name in self.states and self.current_state != self.states[name]:
            if self.current_state_task:
                self.current_state_task.cancel()
            self.current_state = self.states[name]
            self.current_state_task = asyncio.create_task(
                self.current_state.run())

    async def cancel_transition(self):
        if self.current_state_task and not self.current_state_task.done():
            self.current_state_task.cancel()

    async def run(self):
        if not self.current_state_task:
            return
        try:
            await self.current_state_task
        except asyncio.CancelledError:
            pass
