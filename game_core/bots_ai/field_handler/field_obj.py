from enum import Enum, auto

from game_core.game_engine.field import wall
from game_core.game_engine.global_env.enums import Directions
from game_core.game_engine.global_env.types import Position


class BotCellTypes(Enum):
    NoneCell = auto()
    Cell = auto()
    CellRiver = auto()

    CellRiverTop = auto()
    CellRiverBottom = auto()
    CellRiverLeft = auto()
    CellRiverRight = auto()

    CellRiverMouth = auto()
    CellExit = auto()
    CellClinic = auto()
    CellArmory = auto()
    CellArmoryExplosive = auto()
    CellArmoryWeapon = auto()
    UnknownCell = auto()
    PossibleExit = auto()


class BotCell:
    """
    Bot Cell object

    :ivar position: cell position
    :type position: Position
    :ivar type: cell type
    :type type: BotCellTypes
    :ivar direction: river direction (need to be replaced with diff RiverCell types)
    :type direction: Directions | None
    :ivar walls: cell walls
    :type walls: dict[Directions, wall.WallEmpty]
    """
    def __init__(self, position: Position, cell_type: BotCellTypes,
                 direction: Directions | None = None, walls: dict[Directions, wall.WallEmpty] = None):
        self.position = position
        self.type = cell_type
        self.direction = direction  # fixme remove after refactoring
        self.walls = walls or self._gen_default_walls()

    def add_wall(self, direction: Directions, new_wall: wall.WallEmpty):
        """add wall by direction"""
        self.walls[direction] = new_wall

    def __repr__(self):
        match self.type:
            case BotCellTypes.NoneCell:
                return '='
            case BotCellTypes.Cell:
                return 'c'
            case BotCellTypes.CellRiver:
                match self.direction:
                    case Directions.top:
                        return '↑'
                    case Directions.bottom:
                        return '↓'
                    case Directions.right:
                        return '→'
                    case Directions.left:
                        return '←'
                    case _:
                        return 'r'
            case BotCellTypes.CellRiverMouth:
                return 'y'
            case BotCellTypes.CellExit:
                return '⍈'
            case BotCellTypes.CellClinic:
                return 'H'
            case BotCellTypes.CellArmory:
                return 'A'
            case BotCellTypes.CellArmoryExplosive:
                return 'E'
            case BotCellTypes.CellArmoryWeapon:
                return 'W'
            case BotCellTypes.UnknownCell:
                return '?'
            case BotCellTypes.PossibleExit:
                return '⍰'
            case _:
                return self.type.name

    def _gen_default_walls(self) -> dict[Directions, wall.WallEmpty]:
        match self.type:
            case BotCellTypes.CellExit | BotCellTypes.PossibleExit:  # fixme direction
                walls = {
                    Directions.top: wall.WallOuter(),
                    Directions.right: wall.WallOuter(),
                    Directions.bottom: wall.WallOuter(),
                    Directions.left: wall.WallOuter()
                }
                walls.update({self.direction: wall.WallEntrance()})
                return walls

            case BotCellTypes.UnknownCell:
                return {
                    Directions.top: UnknownWall(),
                    Directions.right: UnknownWall(),
                    Directions.bottom: UnknownWall(),
                    Directions.left: UnknownWall()
                }

            case _:
                return {
                    Directions.top: wall.WallEmpty(),
                    Directions.right: wall.WallEmpty(),
                    Directions.bottom: wall.WallEmpty(),
                    Directions.left: wall.WallEmpty()
                }


class UnknownWall(wall.WallEmpty):
    def __init__(self):
        super().__init__()


class UnbreakableWall(wall.WallOuter):
    def __init__(self):
        super().__init__()
