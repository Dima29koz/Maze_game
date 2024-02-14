from typing import Type

from ..game_engine.field import cell
from ..game_engine.global_env.enums import Directions
from .field_handler.field_obj import UnknownCell
from .field_handler.field_state import FieldState


def is_node_is_real(
        n_field: list[list[cell.Cell | cell.CellRiver | None]],
        real_field: list[list[cell.Cell | cell.CellRiver | None]],
        unique_objects_amount: dict[Type[cell.CELL], int]
):
    for y, row in enumerate(real_field):
        for x, real_cell in enumerate(row):
            target_cell = n_field[y][x]
            if real_cell is None and type(target_cell) is cell.NoneCell:
                continue
            if type(target_cell) is cell.NoneCell and type(real_cell) is cell.CellExit:
                continue
            if type(target_cell) is UnknownCell:
                if type(real_cell) in unique_objects_amount:
                    if unique_objects_amount.get(type(real_cell)) > 0:
                        unique_objects_amount[type(real_cell)] -= 1
                    else:
                        return False
                continue
            if type(target_cell) is type(real_cell):
                if type(real_cell) in unique_objects_amount:
                    if unique_objects_amount.get(type(real_cell)) > 0:
                        unique_objects_amount[type(real_cell)] -= 1
                    else:
                        return False
                if type(target_cell) is cell.CellRiver:
                    idx = real_cell.river.index(real_cell)
                    if target_cell.direction is not (real_cell - real_cell.river[idx + 1]):
                        return False
                continue
            else:
                return False
    return True


def is_node_is_valid(node: FieldState):
    for row in node.field.get_field():
        for cell_obj in row:
            if type(cell_obj) is cell.CellRiverMouth:
                may_have_input = False
                for direction in Directions:
                    neighbour = node.field.get_cell(cell_obj.position.get_adjacent(direction))
                    if neighbour:
                        if type(neighbour) is cell.CellRiver and neighbour.direction is -direction:
                            may_have_input = True
                        if type(neighbour) is UnknownCell:
                            may_have_input = True
                if not may_have_input:
                    return False
    return True
