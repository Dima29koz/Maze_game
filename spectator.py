import pygame
from pygame.locals import *
from field.cell import *
from field.wall import *
from field.field import Field
from entities.player import Player
from enums import Directions, Actions, TreasureTypes

RES = WIDTH, HEIGHT = 1202, 902
TILE = 50
cols, rows = 5, 4

pygame.init()
pygame.font.init()
sc = pygame.display.set_mode(RES)
clock = pygame.time.Clock()

field = Field()
grid_cells = field.get_field()


def convert_keys(key) -> Optional[tuple[Actions, Optional[Directions]]]:
    if key:
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

    return


def get_cell_color(cell):
    if type(cell) is CellExit:
        return 55, 120, 20
    if type(cell) is CellRiver:
        return 62, 105, len(cell.river) * 30
    else:
        return 107, 98, 60


def get_wall_color(wall):
    if type(wall) is WallOuter:
        return 60, 45, 15
    if type(wall) is WallConcrete:
        return 170, 105, 25
    if type(wall) is WallExit:
        return 54, 171, 28
    if type(wall) is WallRubber:
        return 15, 15, 15
    else:
        return 'darkslategray'


def draw_field():
    for row in grid_cells:
        for cell in row:
            if cell:
                draw_cell(cell)
                draw_walls(cell)


def draw_cell(cell):
    x, y = cell.x * TILE, cell.y * TILE
    pygame.draw.rect(sc, pygame.Color(get_cell_color(cell)), (x + 2, y + 2, TILE - 2, TILE - 2))
    if type(cell) == CellRiver:
        draw_river_dir(cell, x, y)
    if type(cell) == CellClinic:
        draw_clinic(x, y)
    if isinstance(cell, CellArmory):
        draw_armory(cell, x, y)


def draw_clinic(x, y):
    f1 = pygame.font.Font(None, TILE)
    text = f1.render('H', True, (155, 15, 15))
    place = text.get_rect(center=(x + TILE // 2, y + TILE // 2))
    sc.blit(text, place)


def draw_armory(cell, x, y):
    s = 'A'
    if type(cell) == CellArmoryExplosive:
        s += 'E'
    if type(cell) == CellArmoryWeapon:
        s += 'W'
    f1 = pygame.font.Font(None, TILE * 4 // 5)
    text = f1.render(s, True, (180, 180, 180))
    place = text.get_rect(center=(x + TILE // 2, y + TILE // 2))
    sc.blit(text, place)


def draw_treasures():
    treasures = field.get_treasures()
    for treasure in treasures:
        x, y = treasure.cell.x * TILE, treasure.cell.y * TILE
        if treasure.t_type is TreasureTypes.very:
            pygame.draw.rect(sc, pygame.Color(209, 171, 0),
                             (x + TILE // 3 + 2, y + TILE // 3 + 2, TILE // 3 - 2, TILE // 3 - 2))
        if treasure.t_type is TreasureTypes.spurious:
            pygame.draw.rect(sc, pygame.Color(87, 201, 102),
                             (x + TILE // 3 + 2, y + TILE // 3 + 2, TILE // 3 - 2, TILE // 3 - 2))
        if treasure.t_type is TreasureTypes.mined:
            pygame.draw.rect(sc, pygame.Color(201, 92, 87),
                             (x + TILE // 3 + 2, y + TILE // 3 + 2, TILE // 3 - 2, TILE // 3 - 2))


def draw_players():
    players = field.get_players()
    for player in players:
        x, y = player.cell.x * TILE + TILE // 2, player.cell.y * TILE + TILE // 2
        pygame.draw.circle(sc, pygame.Color("red"), (x, y), TILE // 4)
        if player.treasure:
            x, y = player.cell.x * TILE, player.cell.y * TILE
            if player.treasure.t_type is TreasureTypes.very:
                pygame.draw.rect(sc, pygame.Color(209, 171, 0),
                                 (x + TILE // 3 + 2, y + TILE // 3 + 2, TILE // 3 - 2, TILE // 3 - 2))
            if player.treasure.t_type is TreasureTypes.spurious:
                pygame.draw.rect(sc, pygame.Color(87, 201, 102),
                                 (x + TILE // 3 + 2, y + TILE // 3 + 2, TILE // 3 - 2, TILE // 3 - 2))
            if player.treasure.t_type is TreasureTypes.mined:
                pygame.draw.rect(sc, pygame.Color(201, 92, 87),
                                 (x + TILE // 3 + 2, y + TILE // 3 + 2, TILE // 3 - 2, TILE // 3 - 2))


def draw_river_dir(cell, x, y):
    f1 = pygame.font.Font(None, TILE * 2 // 3)
    s = str(cell.river.index(cell))
    text = f1.render(s, True, (180, 180, 180))
    place = text.get_rect(center=(x + TILE // 2, y + TILE // 2))
    sc.blit(text, place)


def draw_walls(cell: Cell):
    x, y = cell.x * TILE, cell.y * TILE
    pygame.draw.line(sc, get_wall_color(cell.walls[Directions.top]), (x, y), (x + TILE, y), 3)

    pygame.draw.line(sc, get_wall_color(cell.walls[Directions.right]), (x + TILE, y), (x + TILE, y + TILE), 3)

    pygame.draw.line(sc, get_wall_color(cell.walls[Directions.bottom]), (x + TILE, y + TILE), (x, y + TILE), 3)

    pygame.draw.line(sc, get_wall_color(cell.walls[Directions.left]), (x, y + TILE), (x, y), 3)


key = False

while True:
    clock.tick(30)
    sc.fill(pygame.Color('darkslategray'))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
        if event.type == KEYDOWN:
            key = event.key
        if event.type == KEYUP:
            act = convert_keys(key)
            if act:
                field.action_handler(act)
            key = False
            break

    draw_field()
    draw_treasures()
    draw_players()

    pygame.display.flip()
