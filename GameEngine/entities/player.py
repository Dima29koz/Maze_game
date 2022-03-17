from GameEngine.entities.treasure import Treasure
from GameEngine.field.cell import Cell
from GameEngine.globalEnv.Exceptions import PlayerDeath, WinningCondition
from GameEngine.globalEnv.enums import Actions, TreasureTypes

from GameEngine.rules import rules


class Player:
    def __init__(self, cell: Cell, name):
        self.name = name
        self.cell = cell
        self.health_max = rules.get('player_stat').get('max_health')
        self.health = self.health_max
        self.bombs_max = rules.get('player_stat').get('max_bombs')
        self.bombs = self.bombs_max
        self.arrows_max = rules.get('player_stat').get('max_arrows')
        self.arrows = self.arrows_max
        self.treasure: Treasure | None = None
        self.is_alive = True
        self.is_active = False

        self.abilities = {
            Actions.move: True,
            Actions.shoot_bow: True,
            Actions.throw_bomb: True,
            Actions.swap_treasure: False,
            Actions.skip: True,
        }

    def get_allowed_abilities(self, is_tr_under: bool):
        self.abilities[Actions.shoot_bow] = True if self.arrows > 0 else False
        self.abilities[Actions.throw_bomb] = True if self.bombs > 0 else False
        self.abilities[Actions.swap_treasure] = True if (self.can_take_treasure() and is_tr_under) else False
        return self.abilities

    def can_take_treasure(self):
        return self.health == self.health_max

    def take_damage(self):
        self.health -= 1
        if self.health == 0:
            self.is_alive = False
            raise PlayerDeath

    def dropped_treasure(self):
        self.take_damage()
        if self.treasure and self.health <= self.health_max // 2:
            treasure = self.treasure
            treasure.cell = self.cell  # fixme объект меняется внутри объекта
            self.treasure = None
            return treasure

    def throw_bomb(self):
        if self.bombs:
            self.bombs -= 1
            return True
        else:
            return False

    def shoot_bow(self):
        if self.arrows:
            self.arrows -= 1
            return True
        else:
            return False

    def move(self, cell: Cell):
        self.cell = cell

    def heal(self):
        self.health = self.health_max

    def restore_bombs(self):
        self.bombs = self.bombs_max

    def restore_arrows(self):
        self.arrows = self.arrows_max

    def restore_armory(self):
        self.restore_bombs()
        self.restore_arrows()

    def drop_treasure(self):
        if self.treasure:
            treasure = self.treasure
            self.treasure = None
            return treasure

    def came_out_maze(self):
        treasure = self.drop_treasure()
        if treasure and treasure.t_type is TreasureTypes.very:
            raise WinningCondition()
