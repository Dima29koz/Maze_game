from GameEngine.globalEnv.enums import TreasureTypes
from GameEngine.globalEnv.types import Position


class Treasure:
    """
    This is a treasure object

    :param t_type: describe treasure type
    :type t_type: TreasureTypes
    :param position: treasure location
    :type position: Position | None
    """
    def __init__(self, t_type: TreasureTypes, position: Position):
        self.t_type = t_type
        self.position: Position | None = position

    def pick_up(self):
        self.position = None

    def drop(self, position: Position):
        self.position = position

    def to_dict(self):
        res = self.position.to_dict()
        res |= {'type': self.t_type.name}
        return res
