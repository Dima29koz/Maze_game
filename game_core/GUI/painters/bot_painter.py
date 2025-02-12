import pygame

from game_core.bots_ai.field_handler.field_obj import BotCell, BotCellTypes
from game_core.game_engine import Position, Directions
from .painter import Painter
from ..utils import get_bot_cell_color, get_player_color, precompute_bot_cell_text


class BotPainter(Painter):
    def __init__(self, sc: pygame.Surface, tile_size: int):
        super().__init__(sc, tile_size)

    def load_cell_text(self):
        return precompute_bot_cell_text(self.tile_size)

    def draw_cell(self, cell: BotCell, dx: int, dy: int):
        cell_type = cell.type
        if cell_type is BotCellTypes.NoneCell:
            return

        x, y = cell.position.x * self.tile_size + dx, cell.position.y * self.tile_size + dy

        pygame.draw.rect(self.sc, get_bot_cell_color(cell_type),
                         (x + 2, y + 2, self.tile_size - 2, self.tile_size - 2))

        if cell_type is BotCellTypes.CellRiver:
            direction = cell.direction
            if direction is Directions.top:
                cell_type = BotCellTypes.CellRiverTop
            elif direction is Directions.bottom:
                cell_type = BotCellTypes.CellRiverBottom
            elif direction is Directions.right:
                cell_type = BotCellTypes.CellRiverRight
            elif direction is Directions.left:
                cell_type = BotCellTypes.CellRiverLeft
            else:
                raise RuntimeError('unknown direction')

        text = self.cell_text.get(cell_type)
        if text:
            place = text.get_rect(center=(x + self.tile_size // 2, y + self.tile_size // 2))
            self.sc.blit(text, place)

        self.draw_walls(cell.walls, x, y)

    def draw_players(self, players: dict, dx, dy):
        for player in players.items():
            self.draw_player(player, dx, dy)

    def draw_player(self, player: tuple[str, Position], dx: int, dy: int):
        ts = self.tile_size
        player_name, pl_pos = player
        if not pl_pos:
            return
        try:
            td = int(player_name[-1]) + 1
        except Exception:
            td = 1
        x, y = pl_pos.get()
        x = x * ts + dx + (0 if td % 2 == 1 else ts // 2)
        y = y * ts + dy + (0 if td < 3 else ts // 2)
        pygame.draw.rect(self.sc, get_player_color(player_name), (x + 2, y + 2, ts // 2 - 4, ts // 2 - 4), 2)

    def draw_treasures(self, treasures: list[Position], dx, dy):
        for treasure in treasures:
            x, y = treasure.x * self.tile_size + dx, treasure.y * self.tile_size + dy
            self.draw_treasure(None, x, y)
