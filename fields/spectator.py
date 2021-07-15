import pygame
from pygame.locals import *
from cell import *
from field import Field
from player import Player

RES = WIDTH, HEIGHT = 1202, 902
TILE = 50
cols, rows = 5, 4

pygame.init()
sc = pygame.display.set_mode(RES)
clock = pygame.time.Clock()

field = Field(rows, cols)
grid_cells = field.get_grid()
current_cell = grid_cells[0]
# current_cell.remove_walls(grid_cells[1])
player1 = Player(grid_cells[5])


def draw_player(player):
    x, y = player.cell.x * TILE + TILE // 2, player.cell.y * TILE + TILE // 2
    pygame.draw.circle(sc, pygame.Color("red"), (x, y), TILE // 4)


def convert_dirs(direction):
    if direction:
        if direction == K_UP:
            return Directions.top
        elif direction == K_DOWN:
            return Directions.bottom
        if direction == K_LEFT:
            return Directions.left
        elif direction == K_RIGHT:
            return Directions.right
    return Directions.mouth

def draw_cell(cell):
    x, y = cell.x * TILE, cell.y * TILE
    pygame.draw.rect(sc, pygame.Color(cell.get_color()), (x + 2, y + 2, TILE - 2, TILE - 2))
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

    if isinstance(cell.walls[Directions.top], WallConcrete):
        pygame.draw.line(sc, pygame.Color('darkorange'), (x, y), (x + TILE, y), 3)
    if isinstance(cell.walls[Directions.right], WallConcrete):
        pygame.draw.line(sc, pygame.Color('darkorange'), (x + TILE, y), (x + TILE, y + TILE), 3)
    if isinstance(cell.walls[Directions.bottom], WallConcrete):
        pygame.draw.line(sc, pygame.Color('darkorange'), (x + TILE, y + TILE), (x, y + TILE), 3)
    if isinstance(cell.walls[Directions.left], WallConcrete):
        pygame.draw.line(sc, pygame.Color('darkorange'), (x, y + TILE), (x, y), 3)


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
            if direction == K_SPACE:
                direction = False

            player1.set_direction(convert_dirs(direction))
            field.move_calc(player1)

            direction = False
            break

    for cell in grid_cells:
        draw_cell(cell)
        draw_walls(cell)
    draw_player(player1)


    pygame.display.flip()

