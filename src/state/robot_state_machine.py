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
        self.current_state = self.states["idle"]
        self.transition_task = None

    async def transition_to_state(self, name):
        if self.current_state is not None:
            self.current_state.exit()
        self.current_state = self.states[name]
        self.current_state.enter()
        await asyncio.sleep(0)  # Yield control to the event loop

    async def set_next_state(self, name):
        if name in self.states and self.current_state != self.states[name]:
            if self.transition_task:
                self.transition_task.cancel()
            self.transition_task = asyncio.create_task(
                self.transition_to_state(name))
            await self.transition_task  # Await the transition task

    def cancel_transition(self):
        if self.transition_task and not self.transition_task.done():
            self.transition_task.cancel()

    def run(self):
        if self.transition_task and self.transition_task.done():
            self.transition_task = None
        self.current_state.run()
