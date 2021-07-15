class WallEmpty:
    def __init__(self):
        self.breakable = False


class WallConcrete(WallEmpty):
    def __init__(self):
        super(WallConcrete, self).__init__()
        self.breakable = True
