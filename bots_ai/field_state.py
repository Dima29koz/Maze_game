from copy import deepcopy
from typing import Type

from GameEngine.entities.player import Player
from GameEngine.field import cell, wall
from GameEngine.globalEnv.enums import Directions
from bots_ai.field_obj import UnknownCell


class FieldState:
    """
    contains current field state known by player
    """

    def __init__(self, field: list[list[cell.Cell | None]], player: Player, parent):
        self.field = field
        self.player = player
        self.next_states: list[FieldState] = []
        self.parent: FieldState | None = parent

    def get_current_data(self):
        return self.field, self.player

    def update_cell_type(self, new_type: Type[cell.Cell], pos_x: int, pos_y: int, river_direction: Directions = None):
        neighbours = self.field[pos_y][pos_x].neighbours
        walls = self.field[pos_y][pos_x].walls
        self.field[pos_y][pos_x] = new_type(pos_x, pos_y) if not river_direction else cell.CellRiver(pos_x, pos_y,
                                                                                                     river_direction)
        self.field[pos_y][pos_x].change_neighbours(neighbours)
        self.field[pos_y][pos_x].walls = walls
        for direction in Directions:
            if self.field[pos_y][pos_x].neighbours[direction]:
                self.field[pos_y][pos_x].neighbours[direction].neighbours[-direction] = self.field[pos_y][pos_x]

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
        new_state = FieldState(deepcopy(self.field), deepcopy(self.player), self)
        new_state.update_cell_type(new_type, target_cell.x, target_cell.y, direction)
        if new_state.player.cell != target_cell:
            new_state.player.move(target_cell)
        return new_state
