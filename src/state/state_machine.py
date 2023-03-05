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