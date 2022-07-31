class Position:
    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y

    def __eq__(self, other: 'Position'):
        return self.x == other.x and self.y == other.y

    def get(self):
        return self.x, self.y
