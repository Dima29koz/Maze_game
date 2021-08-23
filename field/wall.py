
class WallEmpty:
    def __init__(self):
        self.breakable = True
        self.weapon_collision = False
        self.player_collision = False
        self.player_state = True  # True if active else False

    def handler(self):
        return self.player_collision, self.player_state, type(self)


class WallConcrete(WallEmpty):
    def __init__(self):
        super().__init__()
        self.weapon_collision = True
        self.player_collision = True


class WallOuter(WallConcrete):
    def __init__(self):
        super().__init__()
        self.breakable = False


class WallExit(WallOuter):
    def __init__(self):
        super().__init__()
        self.player_collision = False

    def handler(self):  # todo выход не должен пропускать без клада
        return super().handler()


class WallEntrance(WallExit):
    def __init__(self):
        super().__init__()


class WallRubber(WallEmpty):
    def __init__(self):
        super().__init__()
        self.weapon_collision = True
        self.player_collision = True
        self.player_state = False
