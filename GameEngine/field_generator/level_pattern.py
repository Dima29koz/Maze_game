
class PatternCell:
    def __init__(self, x, y, is_not_none=True):
        self.visited = False
        self.is_not_none = is_not_none
        self.x, self.y = x, y
