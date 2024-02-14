import pygame
from pygame.locals import *

from .painter import Painter
from ..bots_ai.field_handler.tree_node import Node
from ..game_engine.field.field import Field
from ..game_engine.global_env.enums import Directions, Actions
from ..game_engine.global_env.types import Position, LevelPosition
from .utils import get_key_act
from .button import Button
from .bot_ai_spectator import BotAISpectator
from .config import *

from ..bots_ai.core import BotAI


class SpectatorGUI:
    def __init__(self, field: Field, bot: BotAI = None, fps: int = None):
        self.fps = fps if fps else FPS
        self.res = RES
        self.tile_size = TILE
        self.field = field
        self.num_players = len(self.field.players)
        self.leaves_area_size_y = self.res[1] // self.num_players
        self.grid = self.field.game_map.get_level(LevelPosition(0, 0, 0)).field
        self.grid_size_x = len(self.grid[0])
        self.grid_size_y = len(self.grid)
        self.leaves_start_x = self.grid_size_x * self.tile_size + DIST
        self.node_size_x = self.grid_size_x * TILE_LEAF + DIST
        self.max_nodes_x = ((RES[0] - self.leaves_start_x) // self.node_size_x)
        self.node_size_y = self.grid_size_y * TILE_LEAF + DIST

        pygame.init()
        pygame.font.init()
        self.window = pygame.display.set_mode(RES)
        self.sc = pygame.Surface(RES)
        self.clock = pygame.time.Clock()
        self.painter = Painter(self.sc, self.tile_size)
        self.bot_spectator = BotAISpectator(bot, limit=LIMIT) if bot else None

        up = Button(self.sc, (self.tile_size + BTN_X, self.tile_size + BTN_Y), "↑", Directions.top, self.tile_size)
        down = Button(self.sc, (self.tile_size + BTN_X, self.tile_size * 2 + BTN_Y), "↓", Directions.bottom,
                      self.tile_size)
        left = Button(self.sc, (BTN_X, self.tile_size * 2 + BTN_Y), "←", Directions.left, self.tile_size)
        right = Button(self.sc, (self.tile_size * 2 + BTN_X, self.tile_size * 2 + BTN_Y), "→", Directions.right,
                       self.tile_size)

        take_tr = Button(self.sc, (self.tile_size * 2 + BTN_X, BTN_Y), "Tr", Actions.swap_treasure, self.tile_size)
        skip = Button(self.sc, (BTN_X, BTN_Y), "sk", Actions.skip, self.tile_size)

        moving = Button(self.sc, (self.tile_size * 3 + BTN_X, self.tile_size * 2 + BTN_Y), "mo", Actions.move,
                        self.tile_size)
        shooting = Button(self.sc, (self.tile_size * 3 + BTN_X, BTN_Y), "sh", Actions.shoot_bow, self.tile_size)
        bombing = Button(self.sc, (self.tile_size * 3 + BTN_X, self.tile_size + BTN_Y), "bo", Actions.throw_bomb,
                         self.tile_size)

        moving.is_active = True
        self.buttons = [up, down, left, right, take_tr, skip, moving, shooting, bombing]
        self.buttons_st = [moving, shooting, bombing]
        self.buttons_dirs = [up, down, left, right]

    def draw(self, allowed_actions, active_player: str = None):
        self.sc.fill(BG_COLOR or pygame.Color('darkslategray'))
        self.draw_buttons(allowed_actions)
        self.painter.draw(
            grid=self.grid,
            players=self.field.players,
            treasures=self.field.treasures)
        if self.bot_spectator:
            nodes, nodes_amount = self.bot_spectator.get_real_spawn_leaves(active_player)
            _, amount = self.bot_spectator.get_fields(active_player)
            target_node = None
            if nodes_amount:
                target_node = self.draw_leaves(nodes, start_y=0)
            self.draw_text(f'{active_player} real leaves', f'{nodes_amount} / {amount}', 0)
            target_node = target_node if target_node else nodes[0]
            for i, other_player in enumerate(self.bot_spectator.get_other_players(active_player), 1):
                nodes, nodes_amount = self.bot_spectator.get_compatible_leaves(active_player, other_player)
                # nodes, nodes_amount = self.bot_spectator.get_node_compatible_leaves(other_player, target_node)
                _, amount = self.bot_spectator.get_fields(other_player)
                if nodes_amount:
                    self.draw_leaves(nodes, start_y=self.leaves_area_size_y * i)
                self.draw_text(f'{other_player} comp. leaves', f'{nodes_amount} / {amount}', i)

        self.window.blit(self.sc, self.sc.get_rect())
        pygame.event.pump()
        pygame.display.update()
        self.clock.tick(self.fps)

    def draw_text(self, text, amount, y):
        f1 = pygame.font.Font(None, 25)
        text = f1.render(f'{text}: {amount}', True, (255, 255, 255))
        place = text.get_rect(topleft=(10, HEIGHT - 25 - 25 * y))
        self.sc.blit(text, place)

    def draw_leaves(self, nodes: list[Node], start_y) -> Node | None:
        pygame.draw.line(
            self.sc, (255, 0, 0),
            (self.leaves_start_x, start_y - DIST // 2),
            (self.res[0], start_y - DIST // 2),
            2
        )

        target_node = None
        for i, node in enumerate(nodes):
            slot_x = i % self.max_nodes_x
            slot_y = i // self.max_nodes_x
            field, players, treasures = node.get_current_data()
            x = self.leaves_start_x + slot_x * self.node_size_x
            y = start_y + slot_y * self.node_size_y
            if node.is_real:
                pygame.draw.rect(
                    self.sc, (165, 255, 190),
                    (x, y, self.node_size_x - DIST // 2, self.node_size_y - DIST // 2))
            self.painter.draw(grid=field, players=players, treasures=treasures,
                              start_x=x, start_y=y, tile_size=TILE_LEAF, pl=True)
            pos = pygame.mouse.get_pos()
            if pygame.Rect((x, y, self.node_size_x - DIST, self.node_size_y - DIST)).collidepoint(pos):
                pygame.draw.rect(
                    self.sc, (255, 0, 0),
                    (x, y, self.node_size_x - DIST, self.node_size_y - DIST), 1)
                target_node = node
        return target_node

    def get_action(self, allowed_actions, current_state=Actions.move):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                self.close()

            if event.type == KEYUP:
                return get_key_act(event.key, allowed_actions, current_state)

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                return self.get_click_act(allowed_actions, current_state)

        return None, current_state

    def get_click_act(self, allowed_actions, current_state):
        pos = pygame.mouse.get_pos()
        for button in self.buttons:
            if button.get().collidepoint(pos):
                return self.btn_on_click(button, allowed_actions, current_state)
        return None, current_state

    def btn_on_click(self, button, allowed_actions, current_state):
        if (button not in self.buttons_dirs and allowed_actions[button.action]) \
                or button in self.buttons_dirs:
            if button in self.buttons_st:
                for butt in self.buttons_st:
                    butt.is_active = False
                button.is_active = True
                return self.get_action(allowed_actions, button.action)
            elif button in self.buttons_dirs:
                return (current_state, button.active()), current_state
            else:
                return (button.active(), None), current_state

    @staticmethod
    def close():
        exit()

    def draw_buttons(self, allowed_actions):
        for button in self.buttons:
            if button not in self.buttons_dirs:
                if allowed_actions[button.action]:
                    button.draw()
            else:
                button.draw()
