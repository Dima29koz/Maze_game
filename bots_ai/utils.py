from copy import deepcopy
from typing import Type

from GameEngine.field import cell
from GameEngine.globalEnv.enums import Directions
from bots_ai.exceptions import UnreachableState
from bots_ai.field_obj import UnknownCell
from bots_ai.field_state import FieldState


def get_possible_river_dirs_on_walk(current_cell: cell.Cell, turn_direction: Directions):
    prev_cell = current_cell.neighbours[-turn_direction]
    if type(prev_cell) is cell.CellRiverMouth:
        return [-turn_direction]
    else:  # пришли с реки
        if prev_cell.direction is turn_direction:
            return [dir_ for dir_ in Directions if dir_ is not -turn_direction]
        else:
            return [-turn_direction]


def _calc_possible_river_trajectories(
        node: FieldState, current_cell: cell.Cell,
        type_cell_after_wall_check: Type[cell.Cell],
        type_cell_turn_end: Type[cell.Cell], is_diff_cells: bool, turn_direction: Directions):
    new_states = []

    # ... , река, ...
    if type_cell_after_wall_check is cell.CellRiver and not is_diff_cells:
        if type(current_cell) not in [UnknownCell, cell.CellRiver]:
            raise UnreachableState()
        possible_river_dirs = get_possible_river_dirs_on_walk(current_cell, turn_direction)
        print(possible_river_dirs)
        if type(current_cell) is UnknownCell:
            for direction in possible_river_dirs:
                node.add_modified_leaf(current_cell, type_cell_after_wall_check, direction)
            return
        elif type(current_cell) is cell.CellRiver and current_cell.direction in possible_river_dirs:
            if node.player.cell != current_cell:
                node.player.move(current_cell)
            return
        raise UnreachableState()

    # ... , река-река / река-устье, ...
    possible_len = [1, 2] if type_cell_turn_end is cell.CellRiverMouth else [2]
    for length in possible_len:
        req_cell_type = type_cell_turn_end if length == 1 else cell.CellRiver
        for direction in Directions:
            if type(current_cell.neighbours[direction]) in [req_cell_type, UnknownCell]:
                new_location = current_cell.neighbours[direction]
                if length > 1:
                    for dir_ in Directions:
                        if type(new_location.neighbours[dir_]) in [type_cell_turn_end, UnknownCell]:
                            final_location = new_location.neighbours[dir_]
                            new_node = deepcopy(node)
                            new_node.update_cell_type(req_cell_type, new_location.x, new_location.y)
                            new_node.update_cell_type(type_cell_turn_end, final_location.x, final_location.y)
                            new_node.player.move(final_location)
                            new_states.append(new_node)
                else:
                    new_node = deepcopy(node)
                    new_node.update_cell_type(req_cell_type, new_location.x, new_location.y)
                    new_node.player.move(new_location)
                    new_states.append(new_node)

    return new_states


def _get_possible_river_directions(river_cell: cell.Cell) -> list[Directions]:
    dirs = []

    for direction in Directions:
        neighbour_cell = river_cell.neighbours[direction]
        if neighbour_cell is None:
            continue
        elif type(neighbour_cell) is UnknownCell:
            dirs.append(direction)
        elif type(neighbour_cell) is cell.CellRiver and neighbour_cell.direction is not -direction:
            dirs.append(direction)
        elif type(neighbour_cell) is cell.CellRiverMouth:
            semi_neighbour_cells = []
            has_in_river = False
            for dir_ in Directions:
                if dir_ is -direction:
                    continue
                semi_neighbour_cell = neighbour_cell.neighbours[dir_]
                if type(semi_neighbour_cell) is cell.CellRiver and semi_neighbour_cell.direction is -dir_:
                    has_in_river = True
                semi_neighbour_cells.append(semi_neighbour_cell)  # 3 соседа устья

            has_unknown_neighbour = UnknownCell not in [type(semi_neighbour_cell) for semi_neighbour_cell in
                                                        semi_neighbour_cells]
            if not has_in_river:
                if has_unknown_neighbour:
                    dirs.append(direction)
                else:
                    return [direction]
    return dirs
