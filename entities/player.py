from typing import Optional

from entities.treasure import Treasure
from field.cell import *
from globalEnv.Exepts import PlayerDeath, WinningCondition
from globalEnv.enums import Actions, TreasureTypes


class Player:
    def __init__(self, cell: Cell, name):
        self.name = name
        self.cell = cell
        self.health_max = 2
        self.health = self.health_max
        self.bombs_max = 3
        self.bombs = self.bombs_max
        self.arrows_max = 3
        self.arrows = self.arrows_max
        self.treasure: Optional[Treasure] = None
        self.is_active = False

        self.abilities = {
            Actions.move: True,
            Actions.shoot_bow: True,
            Actions.throw_bomb: True,
            Actions.swap_treasure: False,
            Actions.skip: True,
        }

    def get_allowed_abilities(self):
        return self.abilities

    def can_take_treasure(self):
        if self.health == self.health_max:
            return True
        else:
            return False

    def dropped_treasure(self):
        self.health -= 1
        if self.health == 0:
            raise PlayerDeath
        if self.treasure and self.health <= self.health_max // 2:
            treasure = self.treasure
            treasure.cell = self.cell
            self.treasure = None
            return treasure
        return

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
        return

    def came_out_maze(self):
        treasure = self.drop_treasure()
        if treasure and treasure.t_type is TreasureTypes.very:
            raise WinningCondition()
