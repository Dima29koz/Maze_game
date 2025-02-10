from .field_handler.field_obj import BotCell, BotCellTypes


def is_node_is_real(
        node_field: list[list[BotCell]],
        real_field: list[list[BotCell]],
        unique_objects_amount: dict[BotCellTypes, int]
):
    for y, row in enumerate(real_field):
        for x, real_cell in enumerate(row):
            node_cell = node_field[y][x]
            type_node_cell = node_cell.type
            type_real_cell = real_cell.type
            if type_node_cell is BotCellTypes.NoneCell and type_real_cell is BotCellTypes.NoneCell:
                continue
            if type_node_cell is BotCellTypes.PossibleExit and type_real_cell in [BotCellTypes.CellExit,
                                                                                  BotCellTypes.NoneCell]:
                continue
            if type_node_cell is BotCellTypes.UnknownCell:
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
                if type_node_cell is BotCellTypes.CellRiver:
                    if node_cell.direction is not real_cell.direction:
                        return False
                continue
            else:
                return False
    return True
