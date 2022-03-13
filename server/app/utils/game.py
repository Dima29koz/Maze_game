from GameEngine.field.field import Field
from GameEngine.globalEnv.Exceptions import WinningCondition
from GameEngine.globalEnv.enums import Actions, Directions

rules = {
    'generator_rules': {
        'rows': 4, 'cols': 5,
        'is_rect': True,
        'river_rules': [5, 3],
        'armory': True,
        'treasures': [1, 1, 0],
        'walls': {}
    },
    'host_rules': {},
    'players': ['Skipper', 'tester'],
    'gameplay_rules': {'fast_win': True}
}


class Game:
    def __init__(self):
        self.field: Field | None = None
        self.rules: dict = rules

    def create(self, new_rules=None):
        if new_rules:
            self.rules = new_rules
        self.field = Field(self.rules)

    def make_turn(self, action: Actions = Actions.move, direction: Directions = Directions.right):
        try:
            response = self.field.action_handler(action, direction)
            resp = str(response.get_turn_info()) + ' ' + response.get_info()
            act_pl_abilities = self.field.player_turn_start_handler()
            print(resp)
            return resp

        except WinningCondition as e:
            print(e.message)
            return e.message
