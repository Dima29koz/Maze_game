from copy import deepcopy
from typing import Type

from GameEngine.field import cell, wall
from GameEngine.globalEnv.enums import Directions
from bots_ai.exceptions import UnreachableState
from bots_ai.field_obj import UnknownCell, UnknownWall
from bots_ai.field_state import FieldState


def get_possible_river_dirs_on_walk(current_cell: cell.Cell, turn_direction: Directions):
    prev_cell = current_cell.neighbours[-turn_direction]
    if type(prev_cell) is cell.CellRiverMouth:
        return [-turn_direction]
    else:  # пришли с реки
        if prev_cell.direction is turn_direction:
            return [dir_ for dir_ in Directions if dir_ is not -turn_direction]
        else:
            dir_ = known_input_river_direction(prev_cell)
            if dir_ and dir_ is not -turn_direction:
                return []
            return [-turn_direction]


def _calc_possible_river_trajectories(
        node: FieldState, current_cell: cell.Cell,
        type_cell_after_wall_check: Type[cell.Cell],
        type_cell_turn_end: Type[cell.Cell], is_diff_cells: bool, turn_direction: Directions):
    # ... , река, ...
    if type_cell_after_wall_check is cell.CellRiver and not is_diff_cells:
        if type(current_cell) not in [UnknownCell, cell.CellRiver]:
            raise UnreachableState()
        possible_river_dirs = get_possible_river_dirs_on_walk(current_cell, turn_direction)
        if not possible_river_dirs:
            raise UnreachableState()

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

    # все варианты течения первой клетки (игрока двигает по течению)
    new_states = get_possible_leafs(node, current_cell, turn_direction=turn_direction,
                                    same_type=type_cell_turn_end is type_cell_after_wall_check)

    if type_cell_turn_end is not cell.CellRiverMouth:
        # все варианты течения второй клетки (игрока двигает по течению)
        new_states2: list[FieldState] = []
        for new_state in new_states:
            new_states2 += get_possible_leafs(new_state, new_state.player.cell)
        final_states: list[FieldState] = []
        for new_state in new_states2:
            final_states += get_possible_leafs(new_state, new_state.player.cell, is_final=True)
        if len(final_states) > 1:
            [state.set_parent(node) for state in final_states]
            node.next_states = final_states
        return
    else:  # смыло до устья
        final_states: list[FieldState] = []
        new_states2: list[FieldState] = []
        for new_state in new_states:
            current_cell = new_state.player.cell
            if type(current_cell) is cell.CellRiverMouth:
                final_states.append(new_state)
            else:
                new_states2 += get_possible_leafs(new_state, current_cell)
                if type(current_cell) is UnknownCell:
                    final_states.append(new_state.get_modified_copy(current_cell, type_cell_turn_end))

        for new_state in new_states2:
            current_cell = new_state.player.cell
            final_states.append(new_state.get_modified_copy(current_cell, type_cell_turn_end))
        if len(final_states) > 1:
            [state.set_parent(node) for state in final_states]
            node.next_states = final_states
        return


def get_possible_river_directions(river_cell: cell.Cell, same_type=False) -> list[Directions]:
    dirs = []

    for direction in Directions:
        if type(river_cell.walls[direction]) not in [wall.WallEmpty, UnknownWall]:
            continue
        neighbour_cell = river_cell.neighbours[direction]
        if neighbour_cell is None:
            continue
        elif type(neighbour_cell) is UnknownCell:
            dirs.append(direction)
        elif type(neighbour_cell) is cell.CellRiver and neighbour_cell.direction is not -direction:
            has_in_river = False
            for dir_ in Directions:
                if dir_ is -direction:
                    continue
                semi_neighbour_cell = neighbour_cell.neighbours[dir_]
                if type(semi_neighbour_cell) is cell.CellRiver and semi_neighbour_cell.direction is -dir_:
                    has_in_river = True
            if not has_in_river:
                dirs.append(direction)
        elif type(neighbour_cell) is cell.CellRiverMouth and not same_type:
            semi_neighbour_cells = []
            has_in_river = False
            for dir_ in Directions:
                if dir_ is -direction:
                    continue
                semi_neighbour_cell = neighbour_cell.neighbours[dir_]
                if type(semi_neighbour_cell) is cell.CellRiver and semi_neighbour_cell.direction is -dir_:
                    has_in_river = True
                semi_neighbour_cells.append(semi_neighbour_cell)  # 3 соседа устья

            has_unknown_neighbour = UnknownCell in [type(semi_neighbour_cell) for semi_neighbour_cell in
                                                        semi_neighbour_cells]
            if not has_in_river:
                if has_unknown_neighbour:
                    dirs.append(direction)
                else:
                    return [direction]
    return dirs


def get_possible_leafs(node: FieldState, current_cell: cell.Cell,
                       turn_direction: Directions = None, is_final=False, same_type=False):
    possible_river_dirs = get_possible_river_directions(current_cell, same_type)
    if turn_direction:
        try:
            possible_river_dirs.remove(-turn_direction)
        except ValueError:
            pass
    if type(current_cell) is UnknownCell:
        leaves = [node.get_modified_copy(current_cell, cell.CellRiver, direction)
                  for direction in possible_river_dirs]
        if not is_final:
            for leaf in leaves:
                leaf.player.move(leaf.player.cell.neighbours[leaf.player.cell.direction])
        return leaves
    elif type(current_cell) is cell.CellRiver and current_cell.direction in possible_river_dirs:
        if not is_final:
            node.player.move(current_cell.neighbours[current_cell.direction])
        return [node]
    else:
        raise UnreachableState()


def known_input_river_direction(current_cell: cell.Cell) -> Directions | None:
    for direction in Directions:
        neighbour_cell = current_cell.neighbours[direction]
        if type(neighbour_cell) is cell.CellRiver and neighbour_cell.direction is -direction:
            return neighbour_cell.direction
    return
