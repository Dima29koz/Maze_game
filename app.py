from GUI.spectator import SpectatorGUI
from field.field import Field
from globalEnv.Exceptions import WinningCondition
from globalEnv.enums import Actions
from field.response import RespHandler

FPS = 30
RES = WIDTH, HEIGHT = 1202, 600
TILE = 50

players = ['Skipper', 'tester']

rules = {
    'generator_rules': {'rows': 4, 'cols': 5},
    'host_rules': {},
    'players': players,
    'gameplay_rules': {'fast_win': True}
}


field = Field(rules=rules)
gui = SpectatorGUI(FPS, RES, TILE, field)

is_running = True
state = Actions.move
act_pl_abilities = field.player_turn_start_handler()
while is_running:
    gui.draw(act_pl_abilities)
    act, state = gui.get_action(act_pl_abilities, state)
    if act:
        try:
            response = field.action_handler(*act)
            print(response.get_turn_info(), response.get_info())
            act_pl_abilities = field.player_turn_start_handler()
        except WinningCondition as e:
            print(e.message)
            is_running = False
            gui.close()
