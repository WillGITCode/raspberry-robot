class IdleMode:
    """No motion: asks for nothing, so the loop coasts."""

    def enter(self):
        pass

    def tick(self, inputs):
        return None

    def exit(self):
        pass
