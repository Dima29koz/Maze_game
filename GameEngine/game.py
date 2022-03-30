from GameEngine.field.field import Field
from GameEngine.entities.player import Player
from GameEngine.globalEnv.enums import Actions, Directions


class Game:
    def __init__(self, rules):
        self.field = Field(rules=rules)
        self.is_running = True

    def get_current_player(self) -> Player:
        return self.field.get_active_player()

    def get_allowed_abilities_str(self, player: Player):
        abilities = self.field.get_player_allowed_abilities(player)
        return {ability.name: flag for ability, flag in abilities.items()}

    def get_allowed_abilities(self, player: Player):
        return self.field.get_player_allowed_abilities(player)

    def make_turn(self, player: str, action: str, direction: str | None):
        response = []
        current_player: str = self.get_current_player().name
        if player != current_player:
            return  # fixme

        if not self.get_allowed_abilities(self.get_current_player()).get(Actions[action]):
            return
        resp = self.field.action_handler(Actions[action], Directions[direction] if direction else None)
        response.append((resp, self.get_current_player().name))
        while self.get_current_player().is_bot:
            resp = self.field.action_handler(Actions.skip)
            response.append((resp, self.get_current_player().name))  # fixme
        return response

    def get_players_data(self):
        return self.field.get_players_stat()
