from GameEngine.field.field import Field
from GameEngine.entities.player import Player
from GameEngine.field.response import RespHandler
from GameEngine.globalEnv.enums import Actions, Directions, TreasureTypes


class Game:
    def __init__(self, rules):
        self.field = Field(rules=rules)
        self.field.players = self.field.spawn_bots(rules['bots'])
        self.is_running = False

    def get_current_player(self) -> Player:
        return self.field.get_active_player()

    def get_allowed_abilities_str(self, player: Player):
        abilities = self.field.get_player_allowed_abilities(player)
        return {ability.name: flag for ability, flag in abilities.items()}

    def get_allowed_abilities(self, player: Player):
        return self.field.get_player_allowed_abilities(player)

    def make_turn(self, player: str, action: str, direction: str | None = None) -> tuple[RespHandler | None, Player]:
        current_player = self.get_current_player()
        if player != current_player.name:
            return None, current_player

        if not self.get_allowed_abilities(current_player).get(Actions[action]):
            return None, current_player
        resp = self.field.action_handler(Actions[action], Directions[direction] if direction else None)
        return resp, self.get_current_player()

    def check_win_condition(self, rules):
        if self.field.get_alive_pl_amount() == 1 and rules['gameplay_rules']['fast_win']:
            self.is_running = False
            print('players dead')

        # todo необходимо сообщать о типе вынесенного сокровища
        treasures = self.field.get_treasures_on_exit()
        if treasures:
            for treasure in treasures:
                if treasure.t_type is TreasureTypes.very:
                    self.is_running = False
                print(f'treasure {treasure.t_type}')

    def get_players_data(self):
        return self.field.get_players_stat()
