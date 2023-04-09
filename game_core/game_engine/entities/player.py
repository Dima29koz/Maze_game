from copy import deepcopy

from .treasure import Treasure
from ..field.cell import Cell
from ..global_env.enums import Actions

from ..rules import rules  # fixme rules should be atr of Player instance


class Player:
    """
    This is a player object

    :param name: players name
    :type name: str
    :param cell: players location cell
    :type cell: Cell
    :ivar health_max: players max health
    :type health_max: int
    :ivar health: players current health
    :type health: int
    :ivar bombs_max: players max bombs
    :type bombs_max: int
    :ivar bombs: players current bombs
    :type bombs: int
    :ivar arrows_max: players max arrows
    :type arrows_max: int
    :ivar arrows: players current arrows
    :type arrows: int
    :ivar treasure: players treasure
    :type treasure: Treasure | None
    :ivar is_alive: describe is player alive
    :type is_alive: bool
    :ivar is_active: describe is player active
    :type is_active: bool
    :param is_bot: describe is player bot
    :type is_bot: bool
    :param turn: players turn number
    :type turn: int
    """
    def __init__(self, cell: Cell, name: str, is_bot: bool = False, turn: int = 0):
        self.name = name
        self.cell = cell
        self.spawn_point = deepcopy(self.cell.position)
        self.health_max = rules.get('player_stat').get('max_health')
        self.health = self.health_max
        self.bombs_max = rules.get('player_stat').get('max_bombs')
        self.bombs = self.bombs_max
        self.arrows_max = rules.get('player_stat').get('max_arrows')
        self.arrows = self.arrows_max
        self.treasure: Treasure | None = None
        self.is_alive = True
        self.is_active = False
        self.is_treasure_swapped: bool = False
        self.is_bot = is_bot
        self.turn = turn

    def get_allowed_abilities(self, is_tr_under: bool) -> dict[Actions, bool]:
        """returns dict of players abilities"""
        return {
            Actions.move: True,
            Actions.shoot_bow: True if self.arrows > 0 else False,
            Actions.throw_bomb: True if self.bombs > 0 else False,
            Actions.swap_treasure: True if (self.can_take_treasure() and is_tr_under) else False,
            Actions.skip: True,
            Actions.info: True,
        }

    def can_take_treasure(self) -> bool:
        """return players ability to take treasure"""
        return self.health == self.health_max and not self.is_treasure_swapped

    def take_damage(self) -> Treasure | None:
        """damage player and drop treasure if exists"""
        self.health -= 1
        if self.health == 0:
            self.is_alive = False
        if self.health <= self.health_max // 2:
            return self.drop_treasure()

    def throw_bomb(self) -> bool:
        """reduce player bombs. return true if player has bomb"""
        if self.bombs:
            self.bombs -= 1
            return True
        else:
            return False

    def shoot_bow(self) -> bool:
        """reduce player arrows. return true if player has an arrow"""
        if self.arrows:
            self.arrows -= 1
            return True
        else:
            return False

    def move(self, cell: Cell):
        """change player cell parameter"""
        self.cell = cell

    def heal(self):
        """set player health to max"""
        self.health = self.health_max

    def restore_bombs(self):
        """set player bombs to max"""
        self.bombs = self.bombs_max

    def restore_arrows(self):
        """set player arrows to max"""
        self.arrows = self.arrows_max

    def restore_armory(self):
        """set player arrows and bombs to max"""
        self.restore_bombs()
        self.restore_arrows()

    def drop_treasure(self) -> Treasure | None:
        """remove player`s Treasure"""
        if self.treasure:
            treasure = self.treasure
            self.treasure = None
            treasure.drop(self.cell.position)
            return treasure

    def pick_up_treasure(self, treasure: Treasure):
        self.treasure = treasure
        self.treasure.pick_up()
        self.is_treasure_swapped = True

    def on_turn_end(self):
        self.is_active = False
        self.is_treasure_swapped = False

    def to_dict(self) -> dict:
        """convert player object to dict"""
        return {
            'name': self.name,
            'health': self.health,
            'arrows': self.arrows,
            'bombs': self.bombs,
            'has_treasure': True if self.treasure else False,
        }

    def __eq__(self, other):
        return self.name == other.name
