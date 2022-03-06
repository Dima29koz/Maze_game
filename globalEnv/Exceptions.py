class WinningCondition(Exception):
    def __init__(self, message: str = None):
        self.message = message


class PlayerDeath(Exception):
    pass
