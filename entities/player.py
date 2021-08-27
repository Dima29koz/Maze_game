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
            Actions.move: '',
            Actions.shoot_bow: '',
            Actions.throw_bomb: '',
            Actions.swap_treasure: '',
            Actions.skip: True,
        }

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

    def move(self, cell):
        self.cell = cell
        if isinstance(self.cell, CellExit) and self.treasure:
            treasure = self.treasure
            self.treasure = None
            if treasure.t_type is TreasureTypes.very:
                raise WinningCondition()
        elif isinstance(self.cell, CellClinic):
            self.health = self.health_max
        elif isinstance(self.cell, CellArmory):
            self.bombs = self.bombs_max
            self.arrows = self.arrows_max
        elif isinstance(self.cell, CellArmoryWeapon):
            self.arrows = self.arrows_max
        elif isinstance(self.cell, CellArmoryExplosive):
            self.bombs = self.bombs_max
        return [type(self.cell)]
