from GUI.spectator import SpectatorGUI
from field.field import Field
from globalEnv.Exepts import WinningCondition
from globalEnv.enums import Actions
from field.response import RespHandler

FPS = 30
RES = WIDTH, HEIGHT = 1202, 600
TILE = 50

rules = {
    'generator_rules': {'rows': 4, 'cols': 5},
    'host_rules': {},
    'gameplay_rules': {'fast_win': True}
}

field = Field(rules=rules)
gui = SpectatorGUI(FPS, RES, TILE, field)

isRunning = True
state = Actions.move
act_pl_abilities = field.player_turn_start_handler()
while isRunning:
    gui.draw(act_pl_abilities)
    act, state = gui.get_action(act_pl_abilities, state)
    if act:
        try:
            response = field.action_handler(*act)
            print(response.get_turn_info(), response.get_info())
            act_pl_abilities = field.player_turn_start_handler()
        except WinningCondition as e:
            print(e.message)
            isRunning = False
            gui.close()
