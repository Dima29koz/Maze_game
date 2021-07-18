from enums import TreasureTypes
from field.cell import *


class Treasure:
    def __init__(self, t_type: TreasureTypes, cell):
        self.t_type = t_type
        self.cell = cell

    def idle(self):
        if self.cell:
            self.cell.treasure_movement(self)
