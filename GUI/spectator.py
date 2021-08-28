import pygame
from pygame.locals import *
from field.cell import *
from field.wall import *
from field.field import Field
from globalEnv.enums import Directions, Actions, TreasureTypes
from GUI.button import Button


class SpectatorGUI:
    def __init__(self, fps, res: tuple[int, int], tile_size, field: Field):
        self.fps = fps
        self.res = res
        self.tile_size = tile_size
        self.field = field
        pygame.init()
        pygame.font.init()
        self.sc = pygame.display.set_mode(res)
        self.clock = pygame.time.Clock()

        up = Button(self.sc, (self.tile_size+400, 50+300), "↑", Directions.top, self.tile_size)
        down = Button(self.sc, (self.tile_size+400, 100+300), "↓", Directions.bottom, self.tile_size)
        left = Button(self.sc, (0+400, 100+300), "←",  Directions.left, self.tile_size)
        right = Button(self.sc, (self.tile_size * 2+400, 100+300), "→", Directions.right, self.tile_size)

        take_tr = Button(self.sc, (100 + 400, 0 + 300), "Tr", Actions.swap_treasure, self.tile_size)
        skip = Button(self.sc, (0 + 400, 0 + 300), "sk", Actions.skip, self.tile_size)

        moving = Button(self.sc, (150 + 400, 100 + 300), "mo", Actions.move, self.tile_size)
        shooting = Button(self.sc, (150 + 400, 0 + 300), "sh", Actions.shoot_bow, self.tile_size)
        bombing = Button(self.sc, (150 + 400, 50 + 300), "bo", Actions.throw_bomb, self.tile_size)

        moving.is_active = True
        self.buttons = [up, down, left, right, take_tr, skip, moving, shooting, bombing]
        self.buttons_st = [moving, shooting, bombing]
        self.buttons_dirs = [up, down, left, right]

    def draw(self, allowed_actions):
        self.clock.tick(30)
        self.sc.fill(pygame.Color('darkslategray'))
        self.draw_buttons(allowed_actions)
        self.draw_field()
        self.draw_treasures()
        self.draw_players()

        pygame.display.flip()

    def get_action(self, allowed_actions, current_state=Actions.move):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == KEYDOWN and event.key == K_ESCAPE):
                self.close()

            if event.type == KEYUP:
                return self.convert_keys(event.key), current_state

            elif event.type == pygame.MOUSEBUTTONUP:
                pos = pygame.mouse.get_pos()
                for button in self.buttons:
                    if button.get().collidepoint(pos):
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
        return None, current_state

    @staticmethod
    def close():
        exit()

    @staticmethod
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

    @staticmethod
    def get_cell_color(cell):
        if type(cell) is CellExit:
            return 55, 120, 20
        if type(cell) in [CellRiver, CellRiverMouth]:
            return 62, 105, len(cell.river) * 30
        else:
            return 107, 98, 60

    @staticmethod
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

    def draw_buttons(self, allowed_actions):
        for button in self.buttons:
            if button not in self.buttons_dirs:
                if allowed_actions[button.action]:
                    button.draw()
            else:
                button.draw()

    def draw_field(self):
        grid_cells = self.field.get_field()
        for row in grid_cells:
            for cell in row:
                if cell:
                    self.draw_cell(cell)
                    self.draw_walls(cell)

    def draw_cell(self, cell):
        x, y = cell.x * self.tile_size, cell.y * self.tile_size
        pygame.draw.rect(self.sc, pygame.Color(self.get_cell_color(cell)),
                         (x + 2, y + 2, self.tile_size - 2, self.tile_size - 2))
        if type(cell) in [CellRiver, CellRiverMouth]:
            self.draw_river_dir(cell, x, y)
        if type(cell) == CellClinic:
            self.draw_clinic(x, y)
        if isinstance(cell, CellArmory):
            self.draw_armory(cell, x, y)

    def draw_clinic(self, x, y):
        f1 = pygame.font.Font(None, self.tile_size)
        text = f1.render('H', True, (155, 15, 15))
        place = text.get_rect(center=(x + self.tile_size // 2, y + self.tile_size // 2))
        self.sc.blit(text, place)

    def draw_armory(self, cell, x, y):
        s = 'A'
        if type(cell) == CellArmoryExplosive:
            s += 'E'
        if type(cell) == CellArmoryWeapon:
            s += 'W'
        f1 = pygame.font.Font(None, self.tile_size * 4 // 5)
        text = f1.render(s, True, (180, 180, 180))
        place = text.get_rect(center=(x + self.tile_size // 2, y + self.tile_size // 2))
        self.sc.blit(text, place)

    def draw_treasures(self):
        treasures = self.field.get_treasures()
        for treasure in treasures:
            x, y = treasure.cell.x * self.tile_size, treasure.cell.y * self.tile_size
            if treasure.t_type is TreasureTypes.very:
                pygame.draw.rect(self.sc, pygame.Color(209, 171, 0),
                                 (x + self.tile_size // 3 + 2, y + self.tile_size // 3 + 2,
                                  self.tile_size // 3 - 2, self.tile_size // 3 - 2))
            if treasure.t_type is TreasureTypes.spurious:
                pygame.draw.rect(self.sc, pygame.Color(87, 201, 102),
                                 (x + self.tile_size // 3 + 2, y + self.tile_size // 3 + 2,
                                  self.tile_size // 3 - 2, self.tile_size // 3 - 2))
            if treasure.t_type is TreasureTypes.mined:
                pygame.draw.rect(self.sc, pygame.Color(201, 92, 87),
                                 (x + self.tile_size // 3 + 2, y + self.tile_size // 3 + 2,
                                  self.tile_size // 3 - 2, self.tile_size // 3 - 2))

    def draw_players(self):
        players = self.field.get_players()
        for player in players:
            x = player.cell.x * self.tile_size + self.tile_size // 2
            y = player.cell.y * self.tile_size + self.tile_size // 2
            if player.is_active:
                pygame.draw.circle(self.sc, (255, 255, 255),
                                   (x, y), self.tile_size // 3.5)
            pygame.draw.circle(self.sc, pygame.Color(abs(hash(player.name)) % 255, 155, 155),
                               (x, y), self.tile_size // 4)

            if player.treasure:
                x, y = player.cell.x * self.tile_size, player.cell.y * self.tile_size
                if player.treasure.t_type is TreasureTypes.very:
                    pygame.draw.rect(self.sc, pygame.Color(209, 171, 0),
                                     (x + self.tile_size // 3 + 2, y + self.tile_size // 3 + 2,
                                      self.tile_size // 3 - 2, self.tile_size // 3 - 2))
                if player.treasure.t_type is TreasureTypes.spurious:
                    pygame.draw.rect(self.sc, pygame.Color(87, 201, 102),
                                     (x + self.tile_size // 3 + 2, y + self.tile_size // 3 + 2,
                                      self.tile_size // 3 - 2, self.tile_size // 3 - 2))
                if player.treasure.t_type is TreasureTypes.mined:
                    pygame.draw.rect(self.sc, pygame.Color(201, 92, 87),
                                     (x + self.tile_size // 3 + 2, y + self.tile_size // 3 + 2,
                                      self.tile_size // 3 - 2, self.tile_size // 3 - 2))

    def draw_river_dir(self, cell, x, y):
        f1 = pygame.font.Font(None, self.tile_size * 2 // 3)
        s = str(cell.river.index(cell))
        text = f1.render(s, True, (180, 180, 180))
        place = text.get_rect(center=(x + self.tile_size // 2, y + self.tile_size // 2))
        self.sc.blit(text, place)

    def draw_walls(self, cell: Cell):
        x, y = cell.x * self.tile_size, cell.y * self.tile_size
        pygame.draw.line(self.sc, self.get_wall_color(cell.walls[Directions.top]),
                         (x, y), (x + self.tile_size, y), 3)

        pygame.draw.line(self.sc, self.get_wall_color(cell.walls[Directions.right]),
                         (x + self.tile_size, y), (x + self.tile_size, y + self.tile_size), 3)

        pygame.draw.line(self.sc, self.get_wall_color(cell.walls[Directions.bottom]),
                         (x + self.tile_size, y + self.tile_size), (x, y + self.tile_size), 3)

        pygame.draw.line(self.sc, self.get_wall_color(cell.walls[Directions.left]),
                         (x, y + self.tile_size), (x, y), 3)
