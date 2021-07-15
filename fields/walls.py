from logic import dir_calc, Directions


class WallEmpty:
    def __init__(self):
        self.breakable = False

    def handler(self, x, y, direction):
        print("обработчик пустой стены")
        return (*dir_calc(x, y, direction), True)


class WallConcrete(WallEmpty):
    def __init__(self):
        super().__init__()
        self.breakable = True

    def handler(self, x, y, direction):
        print("обработчик каменной стены")
        return (*dir_calc(x, y, Directions.mouth), True)


class WallOuter(WallConcrete):
    def __init__(self):
        super().__init__()
        self.breakable = False

    def handler(self, x, y, direction):
        print("обработчик внешней стены")
        return (*dir_calc(x, y, Directions.mouth), True)
