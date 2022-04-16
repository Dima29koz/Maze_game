from GameEngine.field.cell import Cell
from GameEngine.globalEnv.enums import TreasureTypes


class Treasure:
    """
    This is a treasure object

    :param t_type: describe treasure type
    :type t_type: TreasureTypes
    :param cell: treasure location cell
    :type cell: Cell
    """
    def __init__(self, t_type: TreasureTypes, cell: Cell):
        self.t_type = t_type
        self.cell = cell

    def idle(self):
        """idle handler. change treasure location"""
        if self.cell:
            self.cell = self.cell.treasure_movement()
