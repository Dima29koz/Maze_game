from typing import Type

import pygame
from pygame.locals import *

from ..bots_ai.field_handler.field_obj import BotCellTypes, UnknownWall, UnbreakableWall
from ..game_engine.field import cell as c
from ..game_engine.field import wall as w
from ..game_engine.global_env.enums import Actions, Directions, TreasureTypes


def convert_keys(key) -> tuple[Actions | None, Directions | None]:
    if key == K_SPACE:
        return Actions.skip, None
    if key == K_RETURN:
        return Actions.swap_treasure, None

    if key == K_UP:
        return Actions.move, Directions.top
    if key == K_DOWN:
        return Actions.move, Directions.bottom
    if key == K_LEFT:
        return Actions.move, Directions.left
    if key == K_RIGHT:
        return Actions.move, Directions.right

    if key == K_w:
        return Actions.throw_bomb, Directions.top
    if key == K_s:
        return Actions.throw_bomb, Directions.bottom
    if key == K_a:
        return Actions.throw_bomb, Directions.left
    if key == K_d:
        return Actions.throw_bomb, Directions.right

    if key == K_i:
        return Actions.shoot_bow, Directions.top
    if key == K_k:
        return Actions.shoot_bow, Directions.bottom
    if key == K_j:
        return Actions.shoot_bow, Directions.left
    if key == K_l:
        return Actions.shoot_bow, Directions.right

    return None, None


def get_key_act(key: int | None, allowed_actions, current_state):
    if key:
        action, direction = convert_keys(key)
        if (not action) or not allowed_actions[action]:
            return None, current_state
        return (action, direction), current_state


def get_cell_color(cell: c.CELL):
    if type(cell) is c.CellExit:
        return 55, 120, 20
    if type(cell) in [c.CellRiver, c.CellRiverMouth]:
        return 62, 105, (len(cell.river) * 30) % 255

    return 107, 98, 60


def get_bot_cell_color(cell_type: BotCellTypes):
    if cell_type in (BotCellTypes.CellExit, BotCellTypes.PossibleExit):
        return 55, 120, 20
    if cell_type in (BotCellTypes.CellRiver, BotCellTypes.CellRiverMouth):
        return 62, 105, 75
    if cell_type is BotCellTypes.UnknownCell:
        return 231, 129, 255

    return 107, 98, 60


def get_wall_colors():
    return {
        w.WallOuter: (1, 1, 1),
        w.WallConcrete: (170, 105, 25),
        w.WallExit: (54, 171, 28),
        w.WallEntrance: (54, 171, 28),
        w.WallRubber: (15, 15, 15),
        UnknownWall: (100, 10, 100),
        UnbreakableWall: (60, 45, 15),
        w.WallEmpty: (200, 200, 200)
    }


def get_player_color(player_name: str):
    match player_name:
        case 'Skipper':
            return pygame.Color(255, 1, 1)
        case 'Tester':
            return pygame.Color(1, 255, 1)
        case 'player':
            return pygame.Color(1, 1, 255)
        case 'player_0':
            return pygame.Color(255, 0, 0)
        case 'player_1':
            return pygame.Color(255, 255, 0)
        case 'player_2':
            return pygame.Color(0, 255, 0)
        case 'player_3':
            return pygame.Color(0, 0, 255)
        case _:
            return pygame.Color(
                abs(hash(player_name)) % 255,
                abs(hash(player_name)) % 255,
                abs(hash(player_name)) % 255)


def get_treasure_color(treasure_type: TreasureTypes | None):
    match treasure_type:
        case TreasureTypes.very:
            return pygame.Color(209, 171, 0)
        case TreasureTypes.spurious:
            return pygame.Color(87, 201, 102)
        case TreasureTypes.mined:
            return pygame.Color(201, 92, 87)
        case _:
            return pygame.Color(189, 35, 189)


def precompute_walls(cell_size: int, wall_width: int):
    walls = {}
    for wall_type, color in get_wall_colors().items():
        sc = pygame.Surface((cell_size, wall_width))
        pygame.draw.rect(sc, color,
                         (0, 0, cell_size, wall_width))
        walls |= {wall_type: {'x': sc, 'y': pygame.transform.rotate(sc, 90)}}

    return walls


def precompute_default_walls(cell_size: int, wall_width: int):
    walls = {
        'x': pygame.Surface((cell_size, wall_width)),
        'y': pygame.Surface((wall_width, cell_size))
    }
    pygame.draw.rect(walls['x'], 'darkslategray', (0, 0, cell_size, wall_width))
    pygame.draw.rect(walls['y'], 'darkslategray', (0, 0, wall_width, cell_size))
    return walls


def precompute_cell_text(tile_size) -> dict[Type[c.NoneCell] | str, pygame.Surface]:
    font_full = pygame.font.Font(None, tile_size)
    font_4_5 = pygame.font.Font(None, tile_size * 4 // 5)
    text_color = (180, 180, 180)

    return {
        'CellRiverTop': font_full.render('/\\', True, text_color),
        'CellRiverBottom': font_full.render('\\/', True, text_color),
        'CellRiverRight': font_full.render('>', True, text_color),
        'CellRiverLeft': font_full.render('<', True, text_color),
        c.CellRiverMouth: font_full.render('y', True, text_color),
        c.CellClinic: font_4_5.render('H', True, (155, 15, 15)),
        c.CellArmory: font_4_5.render('A', True, text_color),
        c.CellArmoryWeapon: font_4_5.render('AW', True, text_color),
        c.CellArmoryExplosive: font_4_5.render('AE', True, text_color)
    }


def precompute_bot_cell_text(tile_size) -> dict[BotCellTypes, pygame.Surface]:
    font_full = pygame.font.Font(None, tile_size)
    font_4_5 = pygame.font.Font(None, tile_size * 4 // 5)
    text_color = (180, 180, 180)

    return {
        BotCellTypes.CellRiverTop: font_full.render('/\\', True, text_color),
        BotCellTypes.CellRiverBottom: font_full.render('\\/', True, text_color),
        BotCellTypes.CellRiverRight: font_full.render('>', True, text_color),
        BotCellTypes.CellRiverLeft: font_full.render('<', True, text_color),
        BotCellTypes.CellRiverMouth: font_full.render('y', True, text_color),
        BotCellTypes.PossibleExit: font_full.render('?E', True, text_color),
        BotCellTypes.CellClinic: font_4_5.render('H', True, (155, 15, 15)),
        BotCellTypes.CellArmory: font_4_5.render('A', True, text_color),
        BotCellTypes.CellArmoryWeapon: font_4_5.render('AW', True, text_color),
        BotCellTypes.CellArmoryExplosive: font_4_5.render('AE', True, text_color)
    }
