import pygame

from GUI.utils import get_cell_color, get_wall_color, get_player_color
from GameEngine.field import cell as c
from GameEngine.globalEnv.enums import Directions, TreasureTypes
from GameEngine.globalEnv.types import Position
from bots_ai.field_obj import NoneCell


riv_dirs = {
    Directions.top: '/\\',
    Directions.bottom: '\\/',
    Directions.right: '>',
    Directions.left: '<',
}


class Painter:
    def __init__(self, sc, tile_size: int):
        self.sc = sc
        self.tile_size = tile_size
        self.start_x = 0
        self.start_y = 0

    def draw(self, grid: list[list[c.CELL]] = None, players=None, treasures=None,
             start_x: int = None, start_y: int = None, tile_size: int = None,
             gr=True, pl=True, tr=True):
        dx = start_x if start_x else self.start_x
        dy = start_y if start_y else self.start_y
        ts = tile_size if tile_size else self.tile_size
        if grid and gr:
            self.draw_field(grid, dx, dy, ts)
        if players and pl:
            self.draw_players(players, dx, dy, ts)
        if treasures and tr:
            self.draw_treasures(treasures, dx, dy, ts)

    def draw_field(self, grid: list[list[c.CELL]], dx, dy, ts):
        for row in grid:
            for cell in row:
                if cell and type(cell) is not NoneCell and type(cell) is not c.NoneCell:
                    self.draw_cell(cell, dx, dy, ts)
                    self.draw_walls(cell, dx, dy, ts)

    def draw_cell(self, cell: c.CELL, dx, dy, ts):
        x, y = cell.position.x * ts + dx, cell.position.y * ts + dy
        pygame.draw.rect(self.sc, pygame.Color(get_cell_color(cell)),
                         (x + 2, y + 2, ts - 2, ts - 2))
        if type(cell) in [c.CellRiver, c.CellRiverMouth, c.CellRiverBridge]:
            self.draw_river_dir(cell, x, y, ts)
        if type(cell) == c.CellClinic:
            self.draw_clinic(x, y, ts)
        if isinstance(cell, c.CellArmory):
            self.draw_armory(cell, x, y, ts)

    def draw_river_dir(self, cell, x, y, ts):
        f1 = pygame.font.Font(None, ts * 3 // 3)
        try:
            s = str(cell.river.index(cell))
        except ValueError:
            try:
                s = riv_dirs[cell.direction] if type(cell) is c.CellRiver else 'y'
            except KeyError:
                s = '?' if type(cell) is c.CellRiver else 'y'
        text = f1.render(s, True, (180, 180, 180))
        place = text.get_rect(center=(x + ts // 2, y + ts // 2))
        self.sc.blit(text, place)

    def draw_clinic(self, x, y, ts):
        f1 = pygame.font.Font(None, ts)
        text = f1.render('H', True, (155, 15, 15))
        place = text.get_rect(center=(x + ts // 2, y + ts // 2))
        self.sc.blit(text, place)

    def draw_armory(self, cell, x, y, ts):
        s = 'A'
        if type(cell) == c.CellArmoryExplosive:
            s += 'E'
        if type(cell) == c.CellArmoryWeapon:
            s += 'W'
        f1 = pygame.font.Font(None, ts * 4 // 5)
        text = f1.render(s, True, (180, 180, 180))
        place = text.get_rect(center=(x + ts // 2, y + ts // 2))
        self.sc.blit(text, place)

    def draw_walls(self, cell: c.Cell, dx, dy, ts):
        x, y = cell.position.x * ts + dx, cell.position.y * ts + dy
        pygame.draw.line(self.sc, get_wall_color(cell.walls[Directions.top]),
                         (x, y), (x + ts - 2, y), 2)

        pygame.draw.line(self.sc, get_wall_color(cell.walls[Directions.right]),
                         (x + ts - 2, y), (x + ts - 2, y + ts - 2), 2)

        pygame.draw.line(self.sc, get_wall_color(cell.walls[Directions.bottom]),
                         (x, y + ts - 2), (x + ts - 2, y + ts - 2), 2)

        pygame.draw.line(self.sc, get_wall_color(cell.walls[Directions.left]),
                         (x, y + ts - 2), (x, y), 2)

    def draw_treasures(self, treasures, dx, dy, ts):
        for treasure in treasures:
            x, y = treasure.cell.position.x * ts + dx, treasure.cell.position.y * ts + dy
            self.draw_treasure(treasure, x, y, ts)

    def draw_treasure(self, treasure, x, y, ts):
        if treasure.t_type is TreasureTypes.very:
            pygame.draw.rect(self.sc, pygame.Color(209, 171, 0),
                             (x + ts // 3 + 2, y + ts // 3 + 2,
                              ts // 3 - 2, ts // 3 - 2))
        if treasure.t_type is TreasureTypes.spurious:
            pygame.draw.rect(self.sc, pygame.Color(87, 201, 102),
                             (x + ts // 3 + 2, y + ts // 3 + 2,
                              ts // 3 - 2, ts // 3 - 2))
        if treasure.t_type is TreasureTypes.mined:
            pygame.draw.rect(self.sc, pygame.Color(201, 92, 87),
                             (x + ts // 3 + 2, y + ts // 3 + 2,
                              ts // 3 - 2, ts // 3 - 2))

    def draw_players(self, players: dict | list, dx, dy, ts):
        if type(players) is list:
            for player in players:
                if player.is_alive:
                    self.draw_player(player, dx, dy, ts)
        elif type(players) is dict:
            for player in players.items():
                self.draw_bot_ai_player(*player, dx, dy, ts)

    def draw_player(self, player, dx, dy, ts):
        x = player.cell.position.x * ts + ts // 2 + dx
        y = player.cell.position.y * ts + ts // 2 + dy
        name = player.name
        if player.is_active:
            pygame.draw.circle(self.sc, (255, 255, 255),
                               (x, y), ts // 3.5)
        pygame.draw.circle(self.sc, get_player_color(name),
                           (x, y), ts // 4)

        if player.treasure:
            x, y = player.cell.position.x * ts, player.cell.position.y * ts
            self.draw_treasure(player.treasure, x, y, ts)

    def draw_bot_ai_player(self, player_name, pl_pos, dx, dy, ts):
        if not pl_pos:
            return
        x, y = pl_pos.get()
        x, y = x * ts + dx, y * ts + dy
        pygame.draw.line(self.sc, get_player_color(player_name),
                         (x + 2, y + 2), (x + ts - 2, y + 2), 2)

        pygame.draw.line(self.sc, get_player_color(player_name),
                         (x + ts - 2, y + 2), (x + ts - 2, y + ts - 4), 2)

        pygame.draw.line(self.sc, get_player_color(player_name),
                         (x + ts - 2, y + ts - 4), (x + 2, y + ts - 4), 2)

        pygame.draw.line(self.sc, get_player_color(player_name),
                         (x + 2, y + ts - 4), (x + 2, y + 2), 2)
