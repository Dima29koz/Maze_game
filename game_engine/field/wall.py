
class WallEmpty:
    """
    Base Wall object

    :ivar breakable: can wall be broken
    :type breakable: bool
    :ivar weapon_collision: weapon collision with wall
    :type weapon_collision: bool
    :ivar player_collision: player collision with wall
    :type player_collision: bool
    :ivar player_state: player state after interaction with wall
    :type player_state: bool
    """
    def __init__(self):
        self.breakable = True
        self.weapon_collision = False
        self.player_collision = False
        self.player_state = True  # True if active else False

    def handler(self):
        """returns wall parameters"""
        return self.player_collision, self.player_state, type(self)


class WallConcrete(WallEmpty):
    """Concrete Wall object"""
    def __init__(self):
        super().__init__()
        self.weapon_collision = True
        self.player_collision = True


class WallOuter(WallConcrete):
    """Outer Wall object"""
    def __init__(self):
        super().__init__()
        self.breakable = False


class WallExit(WallOuter):
    """Exit Wall object"""
    def __init__(self):
        super().__init__()
        self.player_collision = False

    def handler(self):  # todo выход не должен пропускать без клада
        return super().handler()


class WallEntrance(WallExit):
    """Entrance Wall object"""
    def __init__(self):
        super().__init__()


class WallRubber(WallEmpty):
    """Rubber Wall object"""
    def __init__(self):
        super().__init__()
        self.weapon_collision = True
        self.player_collision = True
        self.player_state = False
