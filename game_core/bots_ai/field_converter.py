from typing import Type

from game_core.bots_ai.field_handler.field_obj import BotCell, BotCellTypes
from game_core.game_engine.field import cell
from game_core.game_engine.global_env.enums import Directions


def convert_field_from_engine(engine_field: list[list[cell.NoneCell]]) -> list[list[BotCell]]:
    return [[convert_cell_from_engine(obj) for obj in row] for row in engine_field]


def convert_cell_from_engine(engine_cell: cell.CELL) -> BotCell:
    type_bot_cell = convert_cell_type_from_engine(type(engine_cell))
    if type_bot_cell not in [BotCellTypes.CellRiver, BotCellTypes.CellExit]:
        bot_cell = BotCell(engine_cell.position, type_bot_cell)
    elif type_bot_cell is BotCellTypes.CellRiver:
        bot_cell = BotCell(engine_cell.position, type_bot_cell, engine_cell.direction)
    elif type_bot_cell is BotCellTypes.CellExit:
        bot_cell = BotCell(engine_cell.position, type_bot_cell, Directions.top)
    else:
        raise RuntimeError(f'unknown bot cell type `{type_bot_cell}`')
    bot_cell.walls = engine_cell.walls.copy()
    return bot_cell


def convert_cell_type_from_engine(type_engine_cell: Type[cell.CELL]) -> BotCellTypes:
    match type_engine_cell:
        case cell.NoneCell:
            return BotCellTypes.NoneCell
        case cell.Cell:
            return BotCellTypes.Cell
        case cell.CellRiver:
            return BotCellTypes.CellRiver
        case cell.CellRiverMouth:
            return BotCellTypes.CellRiverMouth
        case cell.CellExit:
            return BotCellTypes.CellExit
        case cell.CellClinic:
            return BotCellTypes.CellClinic
        case cell.CellArmory:
            return BotCellTypes.CellArmory
        case cell.CellArmoryExplosive:
            return BotCellTypes.CellArmoryExplosive
        case cell.CellArmoryWeapon:
            return BotCellTypes.CellArmoryWeapon
        case _:
            raise NotImplementedError(f'unknown engine cell type `{type_engine_cell}`')
