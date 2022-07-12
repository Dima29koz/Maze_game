from typing import Type

from GameEngine.field import cell, wall
from GameEngine.globalEnv.enums import Directions
from bots_ai.exceptions import UnreachableState
from bots_ai.field_obj import UnknownCell, UnknownWall
from bots_ai.field_state import FieldState


def _calc_possible_river_trajectories(
        node: FieldState, current_cell: cell.Cell,
        type_cell_after_wall_check: Type[cell.Cell],
        type_cell_turn_end: Type[cell.Cell], is_diff_cells: bool, turn_direction: Directions):
    # ... , река, ...
    if type_cell_after_wall_check is cell.CellRiver and not is_diff_cells:
        if type(current_cell) not in [UnknownCell, cell.CellRiver]:
            raise UnreachableState()
        possible_river_dirs = get_possible_river_directions(current_cell, turn_direction)
        if not possible_river_dirs:
            raise UnreachableState()

        if type(current_cell) is UnknownCell:
            for direction in possible_river_dirs:
                node.add_modified_leaf(current_cell, type_cell_after_wall_check, direction)
            return
        elif type(current_cell) is cell.CellRiver and current_cell.direction in possible_river_dirs:
            if node.player.cell != current_cell:
                node.move_player(current_cell)
            return
        raise UnreachableState()

    # ... , река-река / река-устье, ...

    # все варианты течения первой клетки
    new_states = get_possible_leafs(node, current_cell, turn_direction, washed=True)

    if type_cell_turn_end is not cell.CellRiverMouth:
        # все варианты течения второй клетки
        new_states2: list[FieldState] = []
        for new_state in new_states:
            riv_dir = new_state.player.cell.direction
            new_states2 += get_possible_leafs(new_state, new_state.player.cell.neighbours[riv_dir], riv_dir)
        final_states: list[FieldState] = []
        for new_state in new_states2:
            riv_dir = new_state.player.cell.direction
            final_states += get_possible_leafs(new_state, new_state.player.cell.neighbours[riv_dir], riv_dir)
        if len(final_states) > 1:
            [state.set_parent(node) for state in final_states]
            node.next_states = final_states
        return
    else:  # смыло до устья
        final_states: list[FieldState] = []
        new_states2: list[FieldState] = []
        for new_state in new_states:
            riv_dir = new_state.player.cell.direction
            current_cell = new_state.player.cell.neighbours[riv_dir]
            if type(current_cell) is cell.CellRiverMouth:
                new_state.move_player(current_cell)
                final_states.append(new_state)
            else:
                new_states2 += get_possible_leafs(new_state, current_cell, riv_dir)
                if type(current_cell) is UnknownCell:
                    final_states.append(new_state.get_modified_copy(current_cell, type_cell_turn_end))

        for new_state in new_states2:
            riv_dir = new_state.player.cell.direction
            current_cell = new_state.player.cell.neighbours[riv_dir]
            if type(current_cell) is cell.CellRiverMouth:
                new_state.move_player(current_cell)
                final_states.append(new_state)
            else:
                final_states.append(new_state.get_modified_copy(current_cell, type_cell_turn_end))
        if not (len(final_states) == 1 and final_states[0] is node):
            [state.set_parent(node) for state in final_states]
            node.next_states = final_states
        return


def get_possible_river_directions(river_cell: cell.Cell, turn_direction: Directions = None,
                                  washed: bool = False, next_cell_is_mouth: bool = False) -> list[Directions]:
    dirs = []

    if not washed and turn_direction:
        prev_cell = river_cell.neighbours[-turn_direction]
        if type(prev_cell) is cell.CellRiverMouth or (
           type(prev_cell) is cell.CellRiver and prev_cell.direction is not turn_direction):
            if not has_known_input_river(prev_cell, -turn_direction):
                return [-turn_direction]
            else:
                return []

    for direction in Directions:
        # река не может течь в стену
        if type(river_cell.walls[direction]) not in [wall.WallEmpty, UnknownWall]:
            continue
        neighbour_cell = river_cell.neighbours[direction]
        if neighbour_cell is None:
            continue

        # река не может течь в сушу
        if type(neighbour_cell) not in [cell.CellRiver, cell.CellRiverMouth, UnknownCell]:
            continue

        # реки не могут течь друг в друга
        if type(neighbour_cell) is cell.CellRiver and neighbour_cell.direction is -direction:
            continue

        # река не имеет развилок
        if has_known_input_river(neighbour_cell, direction):
            continue

        if type(neighbour_cell) is cell.CellRiverMouth and is_the_only_allowed_dir(neighbour_cell, direction):
            return [direction]

        # нет стены между соседом, сосед  - река / устье / неизвестная_клетка, в соседа ничего не втекает

        # если смыло, то река не может течь в клетку откуда пришли
        if washed and direction is -turn_direction:
            continue

        dirs.append(direction)
    return dirs


def get_possible_leafs(node: FieldState, current_cell: cell.Cell,
                       turn_direction: Directions = None, is_final: bool = False,
                       washed: bool = False, next_cell_is_mouth: bool = False):
    possible_river_dirs = get_possible_river_directions(current_cell, turn_direction, washed, next_cell_is_mouth)
    if type(current_cell) is UnknownCell:
        leaves = [node.get_modified_copy(current_cell, cell.CellRiver, direction)
                  for direction in possible_river_dirs]
        return leaves
    elif type(current_cell) is cell.CellRiver and current_cell.direction in possible_river_dirs:
        node.move_player(current_cell)
        return [node]
    else:
        raise UnreachableState()


def has_known_input_river(target_cell: cell.Cell, dir_: Directions) -> bool:
    """

    :param target_cell: клетка для которой проверяем
    :param dir_: направление по которому пришли
    :return: True if has known input river
    """
    for direction in Directions:
        if direction is -dir_:
            continue
        neighbour_cell = target_cell.neighbours[direction]
        if type(neighbour_cell) is cell.CellRiver and neighbour_cell.direction is -direction:
            return True


def is_the_only_allowed_dir(target_cell: cell.Cell, dir_: Directions):
    """

    :param target_cell: клетка для которой проверяем
    :param dir_: направление по которому пришли
    :return: True if target cell have only 1 possible direction to input
    """
    for direction in Directions:
        if direction is -dir_:
            continue
        neighbour_cell = target_cell.neighbours[direction]
        if (type(neighbour_cell) is cell.CellRiver and neighbour_cell.direction is -direction) or \
                type(neighbour_cell) is UnknownCell:
            return False
    return True
