from typing import Type

from .field_handler.field_obj import BOT_CELL, UnknownCell, CellRiver, NoneCell, CellExit, PossibleExit


def is_node_is_real(
        node_field: list[list[BOT_CELL]],
        real_field: list[list[BOT_CELL]],
        unique_objects_amount: dict[Type[BOT_CELL], int]
):
    for y, row in enumerate(real_field):
        for x, real_cell in enumerate(row):
            node_cell = node_field[y][x]
            type_node_cell = type(node_cell)
            type_real_cell = type(real_cell)
            if type_node_cell is NoneCell and type_real_cell is NoneCell:
                continue
            if type_node_cell is PossibleExit and type_real_cell in [CellExit, NoneCell]:
                continue
            if type_node_cell is UnknownCell:
                if type_real_cell in unique_objects_amount:
                    if unique_objects_amount.get(type_real_cell) > 0:
                        unique_objects_amount[type_real_cell] -= 1
                    else:
                        return False
                continue
            if type_node_cell is type_real_cell:
                if type_real_cell in unique_objects_amount:
                    if unique_objects_amount.get(type_real_cell) > 0:
                        unique_objects_amount[type_real_cell] -= 1
                    else:
                        return False
                if type_node_cell is CellRiver:
                    if node_cell.direction is not real_cell.direction:
                        return False
                continue
            else:
                return False
    return True
