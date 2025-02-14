from copy import copy
from typing import Union, Type

from .field_obj import BotCell, BotCellTypes, UnknownWall, UnbreakableWall
from ..exceptions import MergingError, OnlyAllowedDir
from ...game_engine.field import wall
from ...game_engine.global_env.enums import Directions
from ...game_engine.global_env.types import Position

R_WALL = Union[
    wall.WallEmpty, wall.WallExit, wall.WallOuter,
    wall.WallEntrance, wall.WallConcrete,
]

WALL = Union[R_WALL, UnbreakableWall, UnknownWall]


class Grid:
    def __init__(self, field: list[list[BotCell]]):
        self._field = field

    def get_field(self) -> list[list[BotCell]]:
        return self._field

    def get_cells(self) -> list[BotCell]:
        cells = []
        for row in self._field:
            cells += row
        return cells

    def get_cell(self, position: Position) -> BotCell:
        return self._field[position.y][position.x]

    def get_cell_by_coords(self, x: int, y: int):
        return self._field[y][x]

    def get_neighbour_cell(self, position: Position, direction: Directions) -> BotCell | None:
        x, y = direction.get_neighbour_cords(position.x, position.y)
        try:
            if x < 0 or y < 0:
                raise IndexError
            return self._field[y][x]
        except IndexError:
            return None

    def set_cell(self,
                 position: Position,
                 cell_type: BotCellTypes,
                 walls: dict[Directions, wall.WallEmpty] = None,
                 direction: Directions = None):
        self._field[position.y][position.x] = BotCell(position, cell_type, direction, walls)

    def copy(self) -> 'Grid':
        return Grid([copy(row) for row in self._field])

    def add_wall(self, position: Position, direction: Directions, wall_type: Type[WALL],
                 neighbour_wall_type: Type[WALL] = None) -> bool:
        cur = self._update_wall(position, direction, wall_type)
        other = False
        neighbour = self.get_neighbour_cell(position, direction)
        if neighbour and neighbour.type is not BotCellTypes.NoneCell:
            if neighbour_wall_type is None:
                neighbour_wall_type = wall_type
            other = self._update_wall(neighbour.position, -direction, neighbour_wall_type)
        return cur or other

    def _update_wall(self, position: Position, direction: Directions, wall_type: Type[WALL]) -> bool:
        cell = self.get_cell(position)
        if type(cell.walls[direction]) is wall_type:
            return False
        cell_walls = cell.walls.copy()
        cell_walls[direction] = wall_type()
        self.set_cell(cell.position, cell.type, cell_walls, cell.direction)
        return True

    def create_exit(self, direction: Directions, position: Position) -> None:
        """

        :param direction: direction of entrance wall
        :param position: position of exit cell
        """
        for dir_ in Directions:
            if dir_ is direction:
                continue
            neighbour_cell = self.get_neighbour_cell(position, dir_)
            if neighbour_cell and neighbour_cell.type is not BotCellTypes.NoneCell:
                if neighbour_cell.type is BotCellTypes.CellExit:
                    continue
                self._update_wall(neighbour_cell.position, -dir_, wall.WallOuter)
        self.get_neighbour_cell(position, direction).add_wall(-direction, wall.WallExit())
        self.set_cell(position, BotCellTypes.CellExit, direction=direction)

    def get_possible_river_directions(self,
                                      river_cell: BotCell,
                                      # todo ensure that river_cell.type is UnknownCell | CellRiver,
                                      turn_direction: Directions = None,
                                      washed: bool = False) -> list[Directions]:
        if not washed and turn_direction:
            prev_cell = self.get_neighbour_cell(river_cell.position, -turn_direction)
            if prev_cell.type is BotCellTypes.CellRiverMouth or (
                    prev_cell.type is BotCellTypes.CellRiver and prev_cell.direction is not turn_direction):
                if not self.has_known_input_river(prev_cell.position, -turn_direction):
                    if self.is_river_is_looped(river_cell.position, prev_cell):
                        return []
                    return [-turn_direction]
                else:
                    return []

        dirs = []
        for direction in Directions:
            # если смыло, то река не может течь в клетку откуда пришли
            if washed and direction is -turn_direction:
                continue

            try:
                if self.is_river_direction_available(river_cell, direction):
                    dirs.append(direction)
            except OnlyAllowedDir:
                return [direction]

        return dirs

    def is_river_direction_available(self,
                                     river_cell: BotCell,  # todo ensure that river_cell.type is UnknownCell | CellRiver
                                     direction: Directions,
                                     no_raise: bool = False):
        """

        :param river_cell: cell to be checked
        :param direction: direction to be checked
        :param no_raise: if True func return True if direction is the only available against raising OnlyAllowedDir exc.
        :return: True if direction is available
        :raises OnlyAllowedDir: if direction is the only allowed
        """
        # река не может течь в стену
        if type(river_cell.walls[direction]) not in [wall.WallEmpty, UnknownWall]:
            return False
        neighbour_cell = self.get_neighbour_cell(river_cell.position, direction)

        # река не может течь в сушу
        if neighbour_cell.type not in [BotCellTypes.CellRiver, BotCellTypes.CellRiverMouth, BotCellTypes.UnknownCell]:
            return False

        # реки не могут течь друг в друга
        if neighbour_cell.type is BotCellTypes.CellRiver and neighbour_cell.direction is -direction:
            return False

        # река не имеет развилок
        if self.has_known_input_river(neighbour_cell.position, direction):
            return False

        if neighbour_cell.type is BotCellTypes.CellRiverMouth and \
                self._is_the_only_allowed_dir(neighbour_cell.position, direction):
            if no_raise:
                return True
            raise OnlyAllowedDir()

        # река не может течь по кругу
        if self.is_river_is_looped(river_cell.position, neighbour_cell):
            return False
        return True

    def is_cause_of_isolated_mouth(self, position: Position) -> bool:
        for direction in Directions:
            neighbour_cell = self.get_neighbour_cell(position, direction)
            if neighbour_cell and neighbour_cell.type is BotCellTypes.CellRiverMouth:
                if self._is_the_only_allowed_dir(neighbour_cell.position, direction):
                    return True
        return False

    def has_known_input_river(self, position: Position, turn_direction: Directions | None, ignore_dir=False) -> bool:
        """

        :param position: position of cell to be checked
        :param turn_direction: direction of turn
        :param ignore_dir: if True all directions will be checked
        :return: True if target_cell has known input river
        """
        neg_direction = -turn_direction if not ignore_dir else None
        for direction in Directions:
            if not ignore_dir and direction is neg_direction:
                continue
            neighbour_cell = self.get_neighbour_cell(position, direction)
            if neighbour_cell and neighbour_cell.type is BotCellTypes.CellRiver and neighbour_cell.direction is -direction:
                return True
        return False

    def _is_the_only_allowed_dir(self, position: Position, turn_direction: Directions) -> bool:
        """

        :param position: position of cell to be checked
        :param turn_direction: direction of turn
        :return: True if target cell have only 1 possible direction to input
        """
        for direction in Directions:
            if direction is -turn_direction:
                continue
            neighbour_cell = self.get_neighbour_cell(position, direction)
            if (neighbour_cell.type is BotCellTypes.CellRiver and neighbour_cell.direction is -direction) or \
                    neighbour_cell.type is BotCellTypes.UnknownCell:
                return False
        return True

    def is_river_is_looped(self, start_position: Position, previous_cell: BotCell) -> bool:
        """

        :param start_position: position to start checking
        :param previous_cell: previous river cell
        :return: True if river is circled
        """
        if start_position == previous_cell.position:
            return True
        if previous_cell.type is BotCellTypes.CellRiver:
            return self.is_river_is_looped(
                start_position, self.get_neighbour_cell(previous_cell.position, previous_cell.direction))
        return False

    @staticmethod
    def is_washed(current_cell: BotCell, prev_cell: BotCell, turn_direction: Directions) -> bool:
        if current_cell is prev_cell:
            return True
        if current_cell.direction is -turn_direction:
            return False
        if prev_cell.type is BotCellTypes.CellRiver and prev_cell.direction is turn_direction:
            return False
        return True

    def merge_with(self,
                   other_field: 'Grid',
                   remaining_obj_amount: dict[BotCellTypes, int]):
        is_changed = False
        for y, row in enumerate(self._field):
            for x, self_cell in enumerate(row):
                other_cell = other_field._field[y][x]
                if self_cell.type is BotCellTypes.NoneCell and other_cell.type is BotCellTypes.NoneCell:
                    continue
                if self_cell.type is BotCellTypes.PossibleExit and other_cell.type in [BotCellTypes.CellExit,
                                                                                       BotCellTypes.NoneCell]:
                    is_changed = True
                    self.merge_cells(other_cell, x, y, no_walls=True)
                if self_cell.type is BotCellTypes.CellExit and other_cell.type is BotCellTypes.PossibleExit:
                    continue
                if self_cell.type is BotCellTypes.UnknownCell and other_cell.type is not BotCellTypes.UnknownCell:
                    if other_cell.type is BotCellTypes.CellRiver:
                        if not self.is_river_direction_available(self_cell, other_cell.direction, no_raise=True):
                            raise MergingError()
                    is_changed = True
                    if other_cell.type in remaining_obj_amount:
                        if remaining_obj_amount.get(other_cell.type) > 0:
                            remaining_obj_amount[other_cell.type] -= 1
                        else:
                            raise MergingError()
                    self.merge_cells(other_cell, x, y)
                new_walls = self.merge_walls(self._field[y][x].walls.copy(), other_cell.walls)
                if new_walls:
                    is_changed = True
                    self._field[y][x] = copy(self._field[y][x])
                    self._field[y][x].walls = new_walls
        if is_changed:
            return self
        return

    def merge_cells(self, other_cell: BotCell, x: int, y: int, no_walls: bool = False):
        self._field[y][x] = copy(other_cell)
        if not no_walls:
            new_walls = self.merge_walls(self._field[y][x].walls.copy(), other_cell.walls)
            if new_walls:
                self._field[y][x].walls = new_walls
        else:
            self._field[y][x].walls = other_cell.walls.copy()

    @staticmethod
    def merge_walls(self_walls: dict[Directions, WALL], other_walls: dict[Directions, WALL]):
        is_changed = False
        for direction in Directions:
            if type(self_walls[direction]) is not type(other_walls[direction]):
                if type(self_walls[direction]) is UnknownWall:
                    is_changed = True
                    self_walls[direction] = copy(other_walls[direction])
                if type(self_walls[direction]) is wall.WallConcrete and type(other_walls[direction]) is wall.WallEmpty:
                    is_changed = True
                    self_walls[direction] = copy(other_walls[direction])
        if is_changed:
            return self_walls
        return
