from pygame.locals import *

from GameEngine.field import cell as c
from GameEngine.field import wall as w
from GameEngine.globalEnv.enums import Actions, Directions
from bots_ai.field_obj import UnknownWall, UnknownCell, UnbreakableWall


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


def get_key_act(key, allowed_actions, current_state):
    if key:
        action, direction = convert_keys(key)
        if (not action) or not allowed_actions[action]:
            return None, current_state
        return (action, direction), current_state


def get_cell_color(cell):
    if type(cell) is c.CellExit:
        return 55, 120, 20
    if type(cell) in [c.CellRiver, c.CellRiverMouth]:
        return 62, 105, (len(cell.river) * 30) % 255
    if type(cell) is UnknownCell:
        return 231, 129, 255
    else:
        return 107, 98, 60


def get_wall_color(wall):
    if type(wall) is w.WallOuter:
        return 1, 1, 1
    if type(wall) is w.WallConcrete:
        return 170, 105, 25
    if type(wall) in [w.WallExit, w.WallEntrance]:
        return 54, 171, 28
    if type(wall) is w.WallRubber:
        return 15, 15, 15
    if type(wall) is UnknownWall:
        return 100, 10, 100
    if type(wall) is UnbreakableWall:
        return 60, 45, 15
    if type(wall) is w.WallEmpty:
        return 200, 200, 200
    else:
        return 'darkslategray'
