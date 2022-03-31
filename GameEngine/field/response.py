from typing import Type

from GameEngine.entities.player import Player
from GameEngine.field.cell import *
from GameEngine.field.wall import *

info = {
    Cell: {'name': {'ru': 'суша'}, 'mechanics': {'ru': ''}},
    CellRiver: {'name': {'ru': 'река'}, 'mechanics': {'ru': ''}},
    CellRiverMouth: {'name': {'ru': 'устье'}, 'mechanics': {'ru': ''}},
    CellExit: {'name': {'ru': 'выход'}, 'mechanics': {'ru': ''}},
    CellClinic: {'name': {'ru': 'Медпункт'}, 'mechanics': {'ru': 'запас здоровья восстановлен'}},
    CellArmory: {'name': {'ru': 'Арсенал'}, 'mechanics': {'ru': 'запас оружия восстановлен'}},
    CellArmoryWeapon: {'name': {'ru': 'Склад оружия'}, 'mechanics': {'ru': 'запас стрел восстановлен'}},
    CellArmoryExplosive: {'name': {'ru': 'Склад взрывчатки'}, 'mechanics': {'ru': 'запас бомб восстановлен'}},

    WallEmpty: {'name': {'ru': 'прошёл', 'en': ''}, 'mechanics': {'ru': ''}},
    WallConcrete: {'name': {'ru': 'стена'}, 'mechanics': {'ru': ''}},
    WallOuter: {'name': {'ru': 'внешняя стена'}, 'mechanics': {'ru': ''}},
    WallRubber: {'name': {'ru': 'резиновая стена'}, 'mechanics': {'ru': ''}},
    WallExit: {'name': {'ru': 'выход'}, 'mechanics': {'ru': ''}},
    WallEntrance: {'name': {'ru': 'вход'}, 'mechanics': {'ru': ''}},
}


class RespHandler:
    def __init__(self):
        self.treasures = False
        self.treasures_amount = 0
        self.cell_type = None
        self.player_name = ''
        self.action = ''
        self.direction = ''

    def update_cell_info(self, treasures_amount: int, cell_type: Type[Cell]):
        if treasures_amount:
            self.treasures = True
            self.treasures_amount = treasures_amount
        self.cell_type = cell_type

    def update_turn_info(self, player_name: str, action_name: str, direction_name: str):
        self.player_name = player_name
        self.action = action_name
        self.direction = direction_name

    def get_info(self):
        if self.treasures:
            res = f', клад ({self.treasures_amount}шт.)'
        else:
            res = ''
        return res + f', {self._translate(self.cell_type, "mechanics")}'

    def get_turn_info(self):
        return {'player_name': self.player_name, 'action': self.action, 'direction': self.direction}

    @staticmethod
    def _translate(obj, rtype='name', lang='ru'):
        return info[obj][rtype][lang]


class RespHandlerSkip(RespHandler):
    def __init__(self, new_location: Type[Cell] = None):
        super().__init__()
        self.new_location = new_location

    def get_info(self):
        res = self._translate(self.new_location)
        tr = super().get_info()
        if tr:
            res += f', {tr}'
        return res


class RespHandlerSwapTreasure(RespHandler):
    def __init__(self, has_treasure: bool):
        super().__init__()
        self.has_treasure = has_treasure

    def get_info(self):
        return 'сменил клад' if self.has_treasure else 'подобрал клад'


class RespHandlerShootBow(RespHandlerSkip):
    def __init__(self, hit: bool,
                 damaged_players: list[Player] = None,
                 dead_players: list[Player] = None,
                 lost_treasure_players: list[Player] = None,
                 new_location: Type[Cell] = None):
        super().__init__(new_location)
        self.hit = hit
        self.damaged_players = damaged_players
        self.dead_players = dead_players
        self.lost_treasure_players = lost_treasure_players

    def get_info(self):
        if self.hit:
            dmg_pl_names = [player.name for player in self.damaged_players]
            tr_lost_pl_names = [player.name for player in self.lost_treasure_players]
            dead_pl_names = [player.name for player in self.dead_players]

            dmg_pl = f' игроки {dmg_pl_names} ранены,' if dmg_pl_names else ''
            dead_pl = f' игроки {dead_pl_names} убиты,' if dead_pl_names else ''
            drop_pl = f' игроки {tr_lost_pl_names} выронили клад' if tr_lost_pl_names else ''
            res = f'попал,{dmg_pl}{dead_pl}{drop_pl}'
        else:
            res = f'не попал,'
        return res + ' ' + super().get_info()


class RespHandlerBombing(RespHandlerSkip):
    def __init__(self, damaged_wall_type: WallEmpty, new_location: Type[Cell] = None):
        super().__init__(new_location)
        self.damaged_wall = damaged_wall_type

    def get_info(self):
        res = 'взорвал' if self.damaged_wall.breakable else 'не взорвал'
        return res + ', ' + super().get_info()


class RespHandlerMoving(RespHandler):
    def __init__(self, wall_type: WallEmpty, cell_after_wall_check: Cell, cell_at_the_turn_ends: Cell):
        super().__init__()
        self.wall_type = wall_type
        self.cell_after_wall_check = cell_after_wall_check
        self.cell_at_the_turn_ends = cell_at_the_turn_ends

    def get_info(self):
        if type(self.cell_after_wall_check) == Cell:
            return f'{self._translate(self.wall_type)}' + \
                   super().get_info()
        if self.cell_after_wall_check == self.cell_at_the_turn_ends:
            return f'{self._translate(self.wall_type)}, ' \
                   f'{self._translate(type(self.cell_at_the_turn_ends))}' + \
                   super().get_info()
        else:
            return f'{self._translate(self.wall_type)}, ' \
                   f'{self._translate(type(self.cell_after_wall_check))}, ' \
                   f'{self._translate(type(self.cell_at_the_turn_ends))}' + \
                   super().get_info()
