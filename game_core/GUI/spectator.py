import pygame
from pygame.locals import *

from .bot_ai_spectator import BotAISpectator
from .button import Button
from .config import GuiConfig, BotAIColors
from .painter import Painter
from .utils import get_key_act
from ..bots_ai.core import BotAI
from ..bots_ai.field_handler.tree_node import Node
from ..game_engine.field.field import Field
from ..game_engine.global_env.enums import Directions, Actions
from ..game_engine.global_env.types import LevelPosition


class SpectatorGUI:
    def __init__(self, field: Field, bot: BotAI = None, fps: int = None):
        self.fps = fps if fps else GuiConfig.FPS
        self.res = GuiConfig.RES
        self.tile_size = GuiConfig.TILE
        self.field = field
        self.num_players = len(self.field.players)
        self.leaves_area_size_y = self.res[1] // self.num_players
        self.grid = self.field.game_map.get_level(LevelPosition(0, 0, 0)).field
        self.grid_size_x = len(self.grid[0])
        self.grid_size_y = len(self.grid)
        self.leaves_start_x = self.grid_size_x * self.tile_size + GuiConfig.DIST
        self.node_size_x = self.grid_size_x * GuiConfig.TILE_LEAF + GuiConfig.DIST
        self.max_nodes_x = ((GuiConfig.RES[0] - self.leaves_start_x) // self.node_size_x)
        self.node_size_y = self.grid_size_y * GuiConfig.TILE_LEAF + GuiConfig.DIST

        pygame.init()
        pygame.font.init()
        self.window = pygame.display.set_mode(GuiConfig.RES)
        self.sc = pygame.Surface(GuiConfig.RES)
        self.clock = pygame.time.Clock()
        self.painter = Painter(self.sc, self.tile_size)
        self.bot_spectator = BotAISpectator(bot, limit=GuiConfig.LIMIT) if bot else None

        up = Button(self.sc, (self.tile_size + GuiConfig.BTN_X, self.tile_size + GuiConfig.BTN_Y), "↑", Directions.top,
                    self.tile_size)
        down = Button(self.sc, (self.tile_size + GuiConfig.BTN_X, self.tile_size * 2 + GuiConfig.BTN_Y), "↓",
                      Directions.bottom,
                      self.tile_size)
        left = Button(self.sc, (GuiConfig.BTN_X, self.tile_size * 2 + GuiConfig.BTN_Y), "←", Directions.left,
                      self.tile_size)
        right = Button(self.sc, (self.tile_size * 2 + GuiConfig.BTN_X, self.tile_size * 2 + GuiConfig.BTN_Y), "→",
                       Directions.right,
                       self.tile_size)

        take_tr = Button(self.sc, (self.tile_size * 2 + GuiConfig.BTN_X, GuiConfig.BTN_Y), "Tr", Actions.swap_treasure,
                         self.tile_size)
        skip = Button(self.sc, (GuiConfig.BTN_X, GuiConfig.BTN_Y), "sk", Actions.skip, self.tile_size)

        moving = Button(self.sc, (self.tile_size * 3 + GuiConfig.BTN_X, self.tile_size * 2 + GuiConfig.BTN_Y), "mo",
                        Actions.move,
                        self.tile_size)
        shooting = Button(self.sc, (self.tile_size * 3 + GuiConfig.BTN_X, GuiConfig.BTN_Y), "sh", Actions.shoot_bow,
                          self.tile_size)
        bombing = Button(self.sc, (self.tile_size * 3 + GuiConfig.BTN_X, self.tile_size + GuiConfig.BTN_Y), "bo",
                         Actions.throw_bomb,
                         self.tile_size)

        moving.is_active = True
        self.buttons = [up, down, left, right, take_tr, skip, moving, shooting, bombing]
        self.buttons_st = [moving, shooting, bombing]
        self.buttons_dirs = [up, down, left, right]

    def draw(self, allowed_actions: dict[Actions, bool], active_player: str = None):
        self.sc.fill(GuiConfig.BG_COLOR or pygame.Color('darkslategray'))
        self.draw_buttons(allowed_actions)
        self.painter.draw(
            grid=self.grid,
            players=self.field.players,
            treasures=self.field.treasures)
        if self.bot_spectator:
            self.draw_bot(active_player)

        self.window.blit(self.sc, self.sc.get_rect())
        pygame.event.pump()
        pygame.display.update()
        self.clock.tick(self.fps)

    def draw_bot(self, active_player: str):
        nodes, nodes_amount = self.bot_spectator.get_real_spawn_leaves(active_player)
        _, amount = self.bot_spectator.get_fields(active_player)
        target_node = None
        if nodes_amount:
            target_node = self.draw_leaves(nodes, start_y=0)
        self.draw_text(f'{active_player} real leaves', f'{nodes_amount} / {amount}', 0)
        target_node = target_node if target_node else nodes[0]
        for i, other_player in enumerate(self.bot_spectator.get_other_players(active_player), 1):
            # nodes, nodes_amount = self.bot_spectator.get_compatible_leaves(active_player, other_player)
            nodes, nodes_amount = self.bot_spectator.get_node_compatible_leaves(other_player, target_node)
            _, amount = self.bot_spectator.get_fields(other_player)
            if nodes_amount:
                self.draw_leaves(nodes, start_y=self.leaves_area_size_y * i)
            self.draw_text(f'{other_player} comp. leaves', f'{nodes_amount} / {amount}', i)

    def draw_text(self, text: str, amount: str, y: int):
        f1 = pygame.font.Font(None, 25)
        text = f1.render(f'{text}: {amount}', True, BotAIColors.WHITE)
        place = text.get_rect(topleft=(10, GuiConfig.HEIGHT - 25 - 25 * y))
        self.sc.blit(text, place)

    def draw_leaves(self, nodes: list[Node], start_y: int) -> Node | None:
        pygame.draw.line(
            self.sc, BotAIColors.RED,
            (self.leaves_start_x, start_y - GuiConfig.DIST // 2),
            (self.res[0], start_y - GuiConfig.DIST // 2),
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
                node_rect = (x - GuiConfig.DIST // 2, y - GuiConfig.DIST // 2, self.node_size_x, self.node_size_y)
                pygame.draw.rect(self.sc, BotAIColors.REAL, node_rect)

            self.painter.draw(grid=field, players=players, treasures=treasures,
                              start_x=x, start_y=y, tile_size=GuiConfig.TILE_LEAF, is_engine=False)

            if self.is_node_hovered(x, y):
                target_node = node
        return target_node

    def is_node_hovered(self, x: int, y: int) -> bool:
        pos = pygame.mouse.get_pos()
        gap = 2
        size_x = self.node_size_x - GuiConfig.DIST + gap
        size_y = self.node_size_y - GuiConfig.DIST + gap

        roi = pygame.Rect((x - gap // 2, y - gap // 2, size_x, size_y))
        if roi.collidepoint(pos):
            pygame.draw.rect(self.sc, BotAIColors.RED, roi, 1)
            return True
        return False

    def get_action(self, allowed_actions: dict[Actions, bool], current_state: Actions = Actions.move):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                self.close()

            if event.type == KEYUP:
                return get_key_act(event.key, allowed_actions, current_state)

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                return self.get_click_act(allowed_actions, current_state)

        return None, current_state

    def get_click_act(self, allowed_actions: dict[Actions, bool], current_state: Actions):
        pos = pygame.mouse.get_pos()
        for button in self.buttons:
            if button.get().collidepoint(pos):
                return self.btn_on_click(button, allowed_actions, current_state)
        return None, current_state

    def btn_on_click(self, button: Button, allowed_actions: dict[Actions, bool], current_state: Actions):
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

    def draw_buttons(self, allowed_actions: dict[Actions, bool]):
        for button in self.buttons:
            if button not in self.buttons_dirs:
                if allowed_actions[button.action]:
                    button.draw()
            else:
                button.draw()
