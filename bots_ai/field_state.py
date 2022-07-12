from copy import deepcopy, copy
from typing import Type

from GameEngine.entities.player import Player
from GameEngine.field import cell, wall
from GameEngine.globalEnv.enums import Directions
from bots_ai.field_obj import UnknownCell


class FieldState:
    """
    contains current field state known by player
    """

    def __init__(self, field: list[list[cell.Cell | None]], player: Player, parent,
                 remaining_unique_obj_types: list,
                 min_x, max_x, min_y, max_y, size_x, size_y, start_x, start_y,
                 is_final_size: bool = False):
        self.field = field
        self.player = player
        self.size_x = size_x
        self.size_y = size_y
        self.start_x = start_x
        self.start_y = start_y
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y
        self.is_final_size = is_final_size
        self.remaining_unique_obj_types = remaining_unique_obj_types
        self.next_states: list[FieldState] = []
        self.parent: FieldState | None = parent

    def get_current_data(self):
        return self.field, self.player

    def move_player(self, target_cell: cell.Cell):
        self.player.move(target_cell)
        if not self.is_final_size and type(target_cell) is not cell.CellExit:
            if target_cell.x > self.max_x:
                self.max_x = target_cell.x
                self.crop_field(Directions.left)
            elif target_cell.x < self.min_x:
                self.min_x = target_cell.x
                self.crop_field(Directions.right)

            if target_cell.y > self.max_y:
                self.max_y = target_cell.y
                self.crop_field(Directions.top)
            elif target_cell.y < self.min_y:
                self.min_y = target_cell.y
                self.crop_field(Directions.bottom)

            if self.max_x - self.min_x == self.size_x and self.max_y - self.min_y == self.size_y:
                self.is_final_size = True

    def crop_field(self, direction: Directions):
        match direction:
            case Directions.top:
                [self.update_cell_type(None, x, self.max_y - self.start_y) for x in range(len(self.field[0]))]
            case Directions.bottom:
                [self.update_cell_type(None, x, self.min_y - self.start_y - 1) for x in range(len(self.field[0]))]
            case Directions.left:
                [self.update_cell_type(None, self.max_x - self.start_x, y) for y in range(len(self.field))]
            case Directions.right:
                [self.update_cell_type(None, self.min_x - self.start_x - 1, y) for y in range(len(self.field))]

    def update_cell_type(self, new_type: Type[cell.Cell] | None, pos_x: int, pos_y: int,
                         river_direction: Directions = None):
        if new_type is None:
            if self.field[pos_y][pos_x] is None or type(self.field[pos_y][pos_x]) is cell.CellExit:
                return
            for direction in Directions:
                if self.field[pos_y][pos_x].neighbours[direction]:
                    self.field[pos_y][pos_x].neighbours[direction].neighbours[-direction] = None
            self.field[pos_y][pos_x] = None
            return

        neighbours = self.field[pos_y][pos_x].neighbours
        walls = self.field[pos_y][pos_x].walls
        self.field[pos_y][pos_x] = new_type(pos_x, pos_y) if not river_direction else cell.CellRiver(pos_x, pos_y,
                                                                                                     river_direction)
        self.field[pos_y][pos_x].change_neighbours(neighbours)
        self.field[pos_y][pos_x].walls = walls
        for direction in Directions:
            if self.field[pos_y][pos_x].neighbours[direction]:
                self.field[pos_y][pos_x].neighbours[direction].neighbours[-direction] = self.field[pos_y][pos_x]
        try:
            self.remaining_unique_obj_types.remove(new_type)
        except ValueError:
            pass

    def create_exit(self, direction: Directions, current_cell: cell.Cell):
        target_cell = current_cell.neighbours[direction]
        if type(target_cell) is not UnknownCell and target_cell is not None:
            return
        cell_exit = cell.CellExit(
            *direction.calc(current_cell.x, current_cell.y), -direction, cell=current_cell)
        current_cell.add_wall(direction, wall.WallExit())
        current_cell.neighbours[direction] = cell_exit
        self.field[cell_exit.y][cell_exit.x] = cell_exit
        return cell_exit

    def remove_leaf(self, leaf):
        self.next_states.remove(leaf)
        if not self.next_states and self.parent:
            self.parent.remove_leaf(self)

    def remove(self):
        self.parent.remove_leaf(self)

    def set_parent(self, node):
        self.parent = node

    def add_modified_leaf(self, target_cell: cell.Cell, new_type: Type[cell.Cell], direction: Directions = None):
        self.next_states.append(self.get_modified_copy(target_cell, new_type, direction))

    def get_modified_copy(self, target_cell: cell.Cell, new_type: Type[cell.Cell], direction: Directions = None):
        new_state = FieldState(deepcopy(self.field), deepcopy(self.player), self, copy(self.remaining_unique_obj_types),
                               self.min_x, self.max_x, self.min_y, self.max_y,
                               self.size_x, self.size_y, self.start_x, self.start_y)
        new_state.update_cell_type(new_type, target_cell.x, target_cell.y, direction)
        if direction:
            new_state.field[target_cell.y][target_cell.x].add_wall(direction, wall.WallEmpty())
            new_state.field[target_cell.y][target_cell.x].neighbours[direction].add_wall(-direction, wall.WallEmpty())
        if new_state.player.cell != new_state.field[target_cell.y][target_cell.x]:
            new_state.move_player(new_state.field[target_cell.y][target_cell.x])
        return new_state
