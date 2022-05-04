from typing import Type

from GameEngine.entities.player import Player
from GameEngine.globalEnv.enums import TreasureTypes
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
    WallExit: {'name': {'ru': 'прошёл'}, 'mechanics': {'ru': ''}},
    WallEntrance: {'name': {'ru': 'прошёл'}, 'mechanics': {'ru': ''}},

    TreasureTypes.very: {'name': {'ru': 'истинный'}, },
    TreasureTypes.spurious: {'name': {'ru': 'ложный'}, },
    TreasureTypes.mined: {'name': {'ru': 'заминированный'}, },
}


class RespHandler:
    """
    Base Response handler object

    :ivar treasures: list of treasures on turn-end cell
    :type treasures: list[TreasureTypes]
    :ivar cell_at_end_of_turn: players location cell on turn-end
    :type cell_at_end_of_turn: Cell | None
    :ivar player_name: name of active player
    :type player_name: str
    :ivar action: players action
    :type action: str
    :ivar direction: players direction
    :type direction: str
    """
    def __init__(self):
        self.treasures: list[TreasureTypes] = []
        self.cell_at_end_of_turn: Cell | None = None
        self.player_name: str = ''
        self.action: str = ''
        self.direction: str = ''

    def set_info(self, turn_end_cell: Cell, treasures: list[TreasureTypes]):
        """Update location and treasures"""
        self.cell_at_end_of_turn = turn_end_cell
        self.treasures = treasures

    def update_turn_info(self, player_name: str, action_name: str, direction_name: str):
        """Update player name, action, direction"""
        self.player_name = player_name
        self.action = action_name
        self.direction = direction_name

    def get_info(self) -> str:
        """returns turn info converted to str"""
        res = ''
        if len(self.treasures) > 0:
            if type(self.cell_at_end_of_turn) == CellExit:
                treasure = self.treasures[0]
                res = f', вынесен {self._translate(treasure)} клад'
            else:
                res = f', клад ({len(self.treasures)}шт.)'
        mechanics_resp = self._translate(type(self.cell_at_end_of_turn), "mechanics")
        if mechanics_resp:
            res += f', {mechanics_resp}'
        return res

    def get_turn_info(self) -> dict:
        """returns turn info converted to dict"""
        return {'player_name': self.player_name, 'action': self.action, 'direction': self.direction}

    @staticmethod
    def _translate(obj: Type[Cell | WallEmpty] | TreasureTypes, rtype='name', lang='ru'):
        return info[obj][rtype][lang]


class RespHandlerSkip(RespHandler):
    """
    Response handler object for action Skip
    """
    def __init__(self):
        super().__init__()

    def get_info(self):
        res = self._translate(type(self.cell_at_end_of_turn))
        return res + super().get_info()


class RespHandlerSwapTreasure(RespHandler):
    """
    Response handler object for action SwapTreasure
    """
    def __init__(self, has_treasure: bool):
        super().__init__()
        self.has_treasure = has_treasure

    def get_info(self):
        return 'сменил клад' if self.has_treasure else 'подобрал клад'


class RespHandlerShootBow(RespHandlerSkip):
    """
    Response handler object for action ShootBow
    """
    def __init__(self,
                 damaged_players: list[Player] = None,
                 dead_players: list[Player] = None,
                 lost_treasure_players: list[Player] = None):
        super().__init__()
        self.hit = True if damaged_players else False
        self.damaged_players = damaged_players
        self.dead_players = dead_players
        self.lost_treasure_players = lost_treasure_players

    def get_info(self):
        if not self.hit:
            return 'не попал, ' + super().get_info()

        dmg_pl_names = [player.name for player in self.damaged_players]
        tr_lost_pl_names = [player.name for player in self.lost_treasure_players]
        dead_pl_names = [player.name for player in self.dead_players]

        dmg_pl = f' игроки {dmg_pl_names} ранены,' if dmg_pl_names else ''
        dead_pl = f' игроки {dead_pl_names} убиты,' if dead_pl_names else ''
        drop_pl = f' игроки {tr_lost_pl_names} выронили клад,' if tr_lost_pl_names else ''
        res = f'попал,{dmg_pl}{dead_pl}{drop_pl} '

        return res + super().get_info()


class RespHandlerBombing(RespHandlerSkip):
    """
    Response handler object for action Bombing
    """
    def __init__(self, damaged_wall_type: WallEmpty):
        super().__init__()
        self.damaged_wall = damaged_wall_type

    def get_info(self):
        res = 'взорвал, ' if self.damaged_wall.breakable else 'не взорвал, '
        return res + super().get_info()


class RespHandlerMoving(RespHandler):
    """
    Response handler object for action Move
    """
    def __init__(self, wall_type: Type[WallEmpty], cell_after_wall_check: Cell):
        super().__init__()
        self.wall_type = wall_type
        self.cell_after_wall_check = cell_after_wall_check

    def get_info(self):
        res = f'{self._translate(self.wall_type)}'
        if self.cell_after_wall_check != self.cell_at_end_of_turn:
            res += f', {self._translate(type(self.cell_after_wall_check))}'
        res += f', {self._translate(type(self.cell_at_end_of_turn))}'
        return res + super().get_info()


class RespHandlerInfo(RespHandler):
    """
    Response handler object for action Info
    """
    def __init__(self):
        super().__init__()

    def get_info(self):
        return self._translate(type(self.cell_at_end_of_turn)) + super().get_info()
