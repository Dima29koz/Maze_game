
class WallEmpty:
    def __init__(self):
        self.breakable = True
        self.weapon_collision = False

    def handler(self):
        """
        Возвращает 2 bool
        state = True if active else False
        moved = True if moved else False
        :return: player_state, moved
        """
        print("пустая стена")

        return True, True


class WallConcrete(WallEmpty):
    def __init__(self):
        super().__init__()
        self.breakable = True
        self.weapon_collision = True

    def handler(self):
        print("каменная стена")
        return True, False


class WallOuter(WallConcrete):
    def __init__(self):
        super().__init__()
        self.breakable = False

    def handler(self):
        print("внешняя стена")
        return True, False


class WallExit(WallOuter):
    def __init__(self):
        super().__init__()

    def handler(self):
        print("выход")
        return True, True


class WallEntrance(WallExit):
    def __init__(self):
        super().__init__()

    def handler(self):
        print("вход")
        return True, True


class WallRubber(WallEmpty):
    def __init__(self):
        super().__init__()
        self.breakable = True
        self.weapon_collision = True

    def handler(self):
        print("резиновая стена")
        return False, False

