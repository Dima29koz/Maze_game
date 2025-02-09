from typing import Type

from game_core.bots_ai.field_handler import field_obj
from game_core.game_engine.field import cell
from game_core.game_engine.global_env.enums import Directions


def convert_field_from_engine(engine_field: list[list[cell.NoneCell]]) -> list[list[field_obj.NoneCell]]:
    return [[convert_cell_from_engine(obj) for obj in row] for row in engine_field]


def convert_cell_from_engine(engine_cell: cell.CELL) -> field_obj.NoneCell:
    type_bot_cell = convert_cell_type_from_engine(type(engine_cell))
    if type_bot_cell not in [field_obj.CellRiver, field_obj.CellExit]:
        bot_cell = type_bot_cell(engine_cell.position)
    elif type_bot_cell is field_obj.CellRiver:
        bot_cell = type_bot_cell(engine_cell.position, engine_cell.direction)
    elif type_bot_cell is field_obj.CellExit:
        bot_cell = field_obj.CellExit(engine_cell.position, Directions.top)
    else:
        raise RuntimeError(f'unknown bot cell type `{type_bot_cell}`')
    bot_cell.walls = engine_cell.walls.copy()
    return bot_cell


def convert_cell_type_from_engine(type_engine_cell: Type[cell.CELL]) -> Type[field_obj.BOT_CELL]:
    match type_engine_cell:
        case cell.NoneCell:
            return field_obj.NoneCell
        case cell.Cell:
            return field_obj.Cell
        case cell.CellRiver:
            return field_obj.CellRiver
        case cell.CellRiverMouth:
            return field_obj.CellRiverMouth
        case cell.CellExit:
            return field_obj.CellExit
        case cell.CellClinic:
            return field_obj.CellClinic
        case cell.CellArmory:
            return field_obj.CellArmory
        case cell.CellArmoryExplosive:
            return field_obj.CellArmoryExplosive
        case cell.CellArmoryWeapon:
            return field_obj.CellArmoryWeapon
        case _:
            raise NotImplementedError(f'unknown engine cell type `{type_engine_cell}`')
