from field.cell import *


class WallEmpty:
    def __init__(self):
        self.breakable = True

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


class WallRubber(WallEmpty):
    def __init__(self):
        super().__init__()
        self.breakable = True

    def handler(self):
        print("резиновая стена")
        return False, False

