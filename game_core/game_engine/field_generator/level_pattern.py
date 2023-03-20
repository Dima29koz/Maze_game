from game_core.game_engine.global_env.types import LevelPosition


class PatternCell:
    def __init__(self, x, y, is_not_none=True):
        self.visited = False
        self.is_not_none = is_not_none
        self.x, self.y = x, y


class LevelPattern:
    def __init__(self, prev_level_pattern: 'LevelPattern', level_position: LevelPosition, gen_rules: dict):
        self.rows: int = gen_rules['rows'] + 2
        self.cols: int = gen_rules['cols'] + 2
        self.is_not_rect: bool = gen_rules['is_not_rect']

        self.level_position: LevelPosition = level_position
        self.pattern: list[list[PatternCell]] = self._gen_pattern(prev_level_pattern)

    def _gen_pattern(self, prev_level_pattern):
        """
        Generates level pattern

        ограничения на форму уровня:
        - хотя бы 1 клетка нового уровня должна находиться над предыдущим

        :param prev_level_pattern:
        :return:
        """
        pattern = [[
            PatternCell(col, row, self._is_in_field(row, col)) for col in range(self.cols)] for row in range(self.rows)]
        if self.is_not_rect:  # todo это заглушка. нужна функция превращающая прямоугольник в облачко с дырками
            self.pattern[3][0].is_not_none = False
            self.pattern[3][3].is_not_none = False
            self.pattern[3][4].is_not_none = False
            self.pattern[1][2].is_not_none = False
        return pattern

    def _is_in_field(self, row: int, col: int) -> bool:
        return row not in [0, self.rows - 1] and col not in [0, self.cols - 1]
