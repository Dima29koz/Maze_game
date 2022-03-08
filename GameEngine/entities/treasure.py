from GameEngine.field.cell import Cell
from GameEngine.globalEnv.enums import TreasureTypes


class Treasure:
    def __init__(self, t_type: TreasureTypes, cell: Cell):
        self.t_type = t_type
        self.cell = cell

    def idle(self):
        if self.cell:
            self.cell = self.cell.treasure_movement()
