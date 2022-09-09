from GameEngine.field.field import Field
from GameEngine.entities.player import Player
from GameEngine.field.response import RespHandler
from GameEngine.globalEnv.enums import Actions, Directions, TreasureTypes
from GameEngine.globalEnv.types import LevelPosition


class Game:
    """
    This class used for top-level interaction with the game object

    :ivar field: game field object which contains all logic and game objects
    :type field: Field
    """
    def __init__(self, rules: dict):
        self.field = Field(rules=rules)
        self.field.players = self.field.spawn_bots(rules['bots_amount'])

    def get_current_player(self) -> Player:
        """returns current Player object"""
        return self.field.get_active_player()

    def get_allowed_abilities_str(self, player: Player) -> dict[str, bool]:
        """returns player allowed abilities converted to dict"""
        abilities = self.field.get_player_allowed_abilities(player)
        return {ability.name: flag for ability, flag in abilities.items()}

    def get_allowed_abilities(self, player: Player) -> dict[Actions, bool] | None:
        """returns player allowed abilities converted to dict"""
        return self.field.get_player_allowed_abilities(player)

    def make_turn(self, action: str, direction: str | None = None) -> tuple[RespHandler | None, Player]:
        """
        active player makes turk with provided action and direction
        checks players ability to make provided action

        :returns: turn response object if action is available, current player object
        """
        current_player = self.get_current_player()
        if not self.get_allowed_abilities(current_player).get(Actions[action]):
            return None, current_player

        resp = self.field.action_handler(Actions[action], Directions[direction] if direction else None)
        return resp, self.get_current_player()

    def is_win_condition(self, rules: dict) -> bool:
        """checks win condition"""
        if self.get_alive_pl_amount() == 1 and rules['gameplay_rules']['fast_win']:
            return True

        for treasure in self.field.get_treasures_on_exit():
            if treasure.t_type is TreasureTypes.very:
                return True

    def get_alive_pl_amount(self) -> int:
        """returns amount of alive players"""
        return len([player for player in self.field.players if player.is_alive])

    def get_players_data(self) -> list[dict]:
        """returns data for players in game"""
        return [player.to_dict() for player in self.field.players]

    def get_players_positions(self) -> list[dict] | list:
        return [player.cell.position.to_dict() | {'name': player.name}
                for player in self.field.players if player.is_alive]

    def get_spawn_point(self, player_name: str) -> dict | None:
        """returns coordinates of player if player is spawned"""
        for player in self.field.players:
            if player.name == player_name:
                return player.spawn_point.to_dict()

    def get_spawn_points(self) -> list[dict] | list:
        try:
            return [{'point': player.spawn_point.to_dict(), 'name': player.name} for player in self.field.players]
        except AttributeError:
            return []

    def get_treasures_list(self) -> list[dict]:
        return [treasure.to_dict() for treasure in self.field.treasures]

    def get_field_list(self) -> list[list[dict]]:
        return self.field.game_map.get_level(LevelPosition(0, 0, 0)).get_field_list()

    def get_field_pattern_list(self) -> list[list[dict | None]]:
        return self.field.game_map.get_level(LevelPosition(0, 0, 0)).get_field_pattern_list()
