from typing import Optional

from enums import Actions, Directions
from entities.treasure import Treasure


class Player:
    def __init__(self, cell):
        self.cell = cell
        self.direction: Directions = Directions.top
        self.health_max = 2
        self.health = self.health_max
        self.bombs_max = 3
        self.bombs = self.bombs_max
        self.arrows_max = 3
        self.arrows = self.arrows_max
        self.treasure: Optional[Treasure] = None

    def action(self, action: Actions, direction: Directions):
        """
        :return: преходит ли ход к следующему игроку
        """
        self.direction = direction
        if action is Actions.skip:
            self.cell.idle(self)
        if action is Actions.move:
            self.cell.check_wall(self)
        if action is Actions.throw_bomb:
            self.throw_bomb()
        if action is Actions.shoot_bow:
            self.shoot_bow()
        return True

    def drop_treasure(self):
        treasure = self.treasure
        self.treasure = None
        return treasure

    def can_take_treasure(self):
        if self.health == self.health_max:
            return True
        else:
            print("только здоровые игроки могут поднять сокровище")
            return False

    def was_hit(self):
        """
        Возвращает True если игрок теряет клад, иначе False
        """
        self.health -= 1
        print("ранен")
        if self.treasure and self.health <= self.health_max // 2:
            print("клад выпал")
            return True
        return False

    def throw_bomb(self):
        if self.bombs:
            self.bombs -= 1
            if self.cell.break_wall(self.direction):
                print("взорвал")
            else:
                print("не взорвал")
        else:
            print("нет бомб")

    def shoot_bow(self):
        if self.arrows:
            self.arrows -= 1
            return True
        else:
            print("нет стрел")
            return False
