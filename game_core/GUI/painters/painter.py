import pygame

from game_core.bots_ai.field_handler.field_obj import BotCell
from game_core.game_engine.entities.player import Player
from game_core.game_engine.entities.treasure import Treasure
from game_core.game_engine.field import cell as c
from game_core.game_engine.global_env.enums import Directions
from game_core.game_engine.global_env.types import Position
from ..utils import (
    get_cell_color, get_player_color, get_treasure_color,
    precompute_walls, precompute_default_walls, precompute_cell_text)


class Painter:
    def __init__(self, sc: pygame.Surface, tile_size: int):
        self.sc = sc
        self.tile_size = tile_size
        self.start_x = 0
        self.start_y = 0

        self._wall_width = 2
        self._cell_size = self.tile_size - self._wall_width * 2

        self.cell_text = self.load_cell_text()
        self._walls = precompute_walls(self._cell_size, self._wall_width)
        self._default_wall = precompute_default_walls(self._cell_size, self._wall_width)

    def load_cell_text(self):
        return precompute_cell_text(self.tile_size)

    def get_wall(self, wall, direction: str):
        return self._walls.get(type(wall), self._default_wall)[direction]

    def draw(self,
             grid: list[list[c.CELL]] | list[list[BotCell]] = None,
             players=None,
             treasures: list[Position] | list[Treasure] = None,
             start_x: int = None, start_y: int = None,
             gr=True, pl=True, tr=True):
        dx = start_x if start_x else self.start_x
        dy = start_y if start_y else self.start_y
        if grid and gr:
            self.draw_field(grid, dx, dy)
        if players and pl:
            self.draw_players(players, dx, dy)
        if treasures and tr:
            self.draw_treasures(treasures, dx, dy)

    def draw_field(self, grid: list[list[c.CELL]] | list[list[BotCell]], dx: int, dy: int):
        for row in grid:
            for cell in row:
                self.draw_cell(cell, dx, dy)

    def draw_cell(self, cell: c.CELL, dx: int, dy: int):
        cell_type = type(cell)
        if cell_type is c.NoneCell:
            return

        x = cell.position.x * self.tile_size + dx
        y = cell.position.y * self.tile_size + dy

        pygame.draw.rect(self.sc, get_cell_color(cell),
                         (x + self._wall_width, y + self._wall_width, self._cell_size, self._cell_size))

        if cell_type is c.CellRiver:
            try:
                if cell.direction is Directions.top:
                    cell_type = 'CellRiverTop'
                elif cell.direction is Directions.bottom:
                    cell_type = 'CellRiverBottom'
                elif cell.direction is Directions.right:
                    cell_type = 'CellRiverRight'
                elif cell.direction is Directions.left:
                    cell_type = 'CellRiverLeft'
            except (KeyError, ValueError):
                raise RuntimeError('unknown direction')

        text = self.cell_text.get(cell_type)
        if text:
            place = text.get_rect(center=(x + self.tile_size // 2, y + self.tile_size // 2))
            self.sc.blit(text, place)

        self.draw_walls(cell.walls, x, y)

    def draw_walls(self, walls: dict, x: int, y: int):
        x_left = x + self._wall_width
        x_right = x_left + self._cell_size
        y_top = y + self._wall_width
        y_bottom = y_top + self._cell_size

        self.sc.blit(self.get_wall(walls[Directions.top], 'x'), (x_left, y))
        self.sc.blit(self.get_wall(walls[Directions.bottom], 'x'), (x_left, y_bottom))
        self.sc.blit(self.get_wall(walls[Directions.left], 'y'), (x, y_top))
        self.sc.blit(self.get_wall(walls[Directions.right], 'y'), (x_right, y_top))

    def draw_treasures(self, treasures: list[Treasure], dx: int, dy: int):
        for treasure in treasures:
            x, y = treasure.position.x * self.tile_size + dx, treasure.position.y * self.tile_size + dy
            self.draw_treasure(treasure.t_type, x, y)

    def draw_treasure(self, treasure_type, x: int, y: int):
        tr_s = self.tile_size // 3
        pygame.draw.rect(self.sc, get_treasure_color(treasure_type),
                         (x + tr_s + 2, y + tr_s + 2,
                          tr_s - 2, tr_s - 2))

    def draw_players(self, players: list, dx: int, dy: int):
        for player in players:
            if player.is_alive:
                self.draw_player(player, dx, dy)

    def draw_player(self, player: Player, dx: int, dy: int):
        ts = self.tile_size
        name = player.name
        try:
            td = int(name[-1]) + 1
        except Exception:
            td = 1
        x_tile = player.cell.position.x * ts
        y_tile = player.cell.position.y * ts
        x = x_tile + ts * (1 if td % 2 == 1 else 3) // 4 + dx
        y = y_tile + ts * (1 if td < 3 else 3) // 4 + dy

        if player.is_active:
            pygame.draw.circle(self.sc, (255, 255, 255),
                               (x, y), ts // 7)
        pygame.draw.circle(self.sc, get_player_color(name),
                           (x, y), ts // 8)

        if player.treasure:
            self.draw_treasure(player.treasure.t_type, x_tile, y_tile)
