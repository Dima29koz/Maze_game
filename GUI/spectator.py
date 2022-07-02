import pygame
from pygame.locals import *

from GUI.painter import Painter
from GameEngine.field.field import Field
from GameEngine.globalEnv.enums import Directions, Actions
from GUI.utils import get_key_act
from GUI.button import Button
from GUI.bot_ai_spectator import BotAISpectator

from bots_ai.turn_state import BotAI

FPS = 30
RES = WIDTH, HEIGHT = 1600, 800
TILE = 50
BTN_X = 0
BTN_Y = 300
DIST = 15
LIMIT = 10


class SpectatorGUI:
    def __init__(self, field: Field, bot: BotAI = None):
        self.fps = FPS
        self.res = RES
        self.tile_size = TILE
        self.field = field
        pygame.init()
        pygame.font.init()
        self.sc = pygame.display.set_mode(RES)
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

    def draw(self, allowed_actions):
        self.clock.tick(self.fps)
        self.sc.fill(pygame.Color('darkslategray'))
        self.draw_buttons(allowed_actions)
        self.painter.draw(grid=self.field.field, players=self.field.players, treasures=self.field.treasures)
        dx = len(self.field.field[0]) * self.tile_size + DIST
        if self.bot_spectator:
            fields, fields_amount = self.bot_spectator.get_fields()
            f1 = pygame.font.Font(None, 25)
            text = f1.render(f'leaves amount: {fields_amount}', True, (255, 255, 255))
            place = text.get_rect(topleft=(10, HEIGHT-25))
            self.sc.blit(text, place)
            f_size_x = len(fields[0][0][0])
            f_size_y = len(fields[0][0])
            tile_size = 30
            i = 0
            start_y = 0
            for field in fields:
                start_x = dx + (f_size_x * tile_size + DIST) * i
                if start_x + f_size_x * tile_size + DIST > RES[0]:
                    i = 0
                    start_y += f_size_y * tile_size + DIST
                    start_x = dx + (f_size_x * tile_size + DIST) * i
                self.painter.draw(grid=field[0], players=[field[1]],
                                  start_x=start_x, start_y=start_y, tile_size=tile_size, pl=False)
                i += 1

        pygame.display.flip()

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
