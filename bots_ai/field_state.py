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
                 remaining_unique_obj_types: list, is_final_size: bool = False):
        self.field = field
        self.player = player
        self.is_final_size = is_final_size
        self.remaining_unique_obj_types = remaining_unique_obj_types
        self.next_states: list[FieldState] = []
        self.parent: FieldState | None = parent

    def get_current_data(self):
        return self.field, self.player

    def crop_field(self, direction: Directions):
        match direction:
            case Directions.top:
                self.field.pop(0)
                [self.update_cell_type(None, x, 0) for x in range(len(self.field[0]))]
            case Directions.bottom:
                self.field.pop(-1)
                [self.update_cell_type(None, x, -1) for x in range(len(self.field[0]))]
            case Directions.left:
                [self.field[row].pop(0) for row in range(len(self.field))]
                [self.update_cell_type(None, 0, y) for y in range(len(self.field))]
            case Directions.right:
                [self.field[row].pop(-1) for row in range(len(self.field))]
                [self.update_cell_type(None, -1, y) for y in range(len(self.field))]

    def update_cell_type(self, new_type: Type[cell.Cell] | None, pos_x: int, pos_y: int,
                         river_direction: Directions = None):
        if new_type is None:
            if self.field[pos_y][pos_x] is None:
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
        new_state = FieldState(deepcopy(self.field), deepcopy(self.player), self, copy(self.remaining_unique_obj_types))
        new_state.update_cell_type(new_type, target_cell.x, target_cell.y, direction)
        if new_state.player.cell != new_state.field[target_cell.y][target_cell.x]:
            new_state.player.move(new_state.field[target_cell.y][target_cell.x])
        return new_state
