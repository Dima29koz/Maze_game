from GUI.spectator import SpectatorGUI
from GameEngine.field.field import Field
from GameEngine.globalEnv.Exceptions import WinningCondition
from GameEngine.globalEnv.enums import Actions

from rules import rules


field = Field(rules=rules)
gui = SpectatorGUI(field)

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
