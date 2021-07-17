import pygame
from pygame.locals import *
from field.cell import *
from field.wall import *
from field.field import Field
from entities.player import Player
from enums import Directions, Actions

RES = WIDTH, HEIGHT = 1202, 902
TILE = 50
cols, rows = 5, 4

pygame.init()
sc = pygame.display.set_mode(RES)
clock = pygame.time.Clock()

field = Field()
grid_cells = field.get_field()

player1 = Player(grid_cells[1][1])


def draw_player(player):
    x, y = player.cell.x * TILE + TILE // 2, player.cell.y * TILE + TILE // 2
    pygame.draw.circle(sc, pygame.Color("red"), (x, y), TILE // 4)


def convert_dirs(key):
    if key:
        if key == K_SPACE:
            return Actions.skip, Directions.mouth
        if key == K_UP:
            return Actions.move, Directions.top
        if key == K_DOWN:
            return Actions.move, Directions.bottom
        if key == K_LEFT:
            return Actions.move, Directions.left
        if key == K_RIGHT:
            return Actions.move, Directions.right
    return False


def get_cell_color(cell):
    if type(cell) is Cell:
        return 107, 98, 60
    if type(cell) is CellRiver:
        return 62, 105, 171


def get_wall_color(wall):
    if type(wall) is WallOuter:
        return 60, 45, 15
    if type(wall) is WallConcrete:
        return 170, 105, 25
    if type(wall) is WallExit:
        return 54, 171, 28
    else:
        return 'darkslategray'


def draw_cell(cell):
    x, y = cell.x * TILE, cell.y * TILE
    pygame.draw.rect(sc, pygame.Color(get_cell_color(cell)), (x + 2, y + 2, TILE - 2, TILE - 2))
    if type(cell) == CellRiver:
        draw_river_dir(cell, x, y)


def draw_river_dir(cell, x, y):
    if cell.direction == Directions.right:
        pygame.draw.polygon(sc, pygame.Color("blue"), [(x + 2, y + TILE // 3 + 2),
                                                       (x + 2, y + TILE // 3 * 2 - 2),
                                                       (x + TILE - 2, y + TILE // 2 - 1)])
    if cell.direction == Directions.top:
        pygame.draw.polygon(sc, pygame.Color("blue"), [(x + TILE // 3 + 2, y + TILE - 2),
                                                       (x + TILE // 3 * 2 - 2, y + TILE - 2),
                                                       (x + TILE // 2, y + 2)])
    if cell.direction == Directions.left:
        pygame.draw.polygon(sc, pygame.Color("blue"), [(x + TILE - 2, y + TILE // 3 + 2),
                                                       (x + TILE - 2, y + TILE // 3 * 2 - 2),
                                                       (x + 2, y + TILE // 2 - 1)])
    if cell.direction == Directions.bottom:
        pygame.draw.polygon(sc, pygame.Color("blue"), [(x + TILE // 3 + 2, y + 2),
                                                       (x + TILE // 3 * 2 - 2, y + 2),
                                                       (x + TILE // 2, y + TILE - 2)])
    if cell.direction == Directions.mouth:
        pygame.draw.circle(sc, pygame.Color("blue"), (x + TILE // 2, y + TILE // 2), TILE // 4)


def draw_walls(cell: Cell):
    x, y = cell.x * TILE, cell.y * TILE
    pygame.draw.line(sc, get_wall_color(cell.walls[Directions.top]), (x, y), (x + TILE, y), 3)

    pygame.draw.line(sc, get_wall_color(cell.walls[Directions.right]), (x + TILE, y), (x + TILE, y + TILE), 3)

    pygame.draw.line(sc, get_wall_color(cell.walls[Directions.bottom]), (x + TILE, y + TILE), (x, y + TILE), 3)

    pygame.draw.line(sc, get_wall_color(cell.walls[Directions.left]), (x, y + TILE), (x, y), 3)


direction = False

while True:
    clock.tick(30)
    sc.fill(pygame.Color('darkslategray'))

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            exit()
        if event.type == KEYDOWN:
            direction = event.key
        if event.type == KEYUP:
            player1.state, player1.direction = convert_dirs(direction)
            player1.action()
            direction = False
            break

    for row in grid_cells:
        for cell in row:
            draw_cell(cell)
            draw_walls(cell)
    draw_player(player1)

    pygame.display.flip()

