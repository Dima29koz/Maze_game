from GUI.spectator import SpectatorGUI
from GameEngine.field.field import Field
from GameEngine.game import Game
from GameEngine.globalEnv.Exceptions import WinningCondition
from GameEngine.globalEnv.enums import Actions

from rules import rules

"""
Сломано! Но работает
"""


def main():
    rules['players'] = ['Skipper', 'Tester']
    field = Game(rules=rules).field
    gui = SpectatorGUI(field)

    is_running = True
    state = Actions.move
    act_pl_abilities = field.get_player_allowed_abilities(field.get_active_player())
    while is_running:
        gui.draw(act_pl_abilities)
        act, state = gui.get_action(act_pl_abilities, state)
        if act:
            try:
                response = field.action_handler(*act)
                print(response.get_turn_info(), response.get_info())
                act_pl_abilities = field.get_player_allowed_abilities(field.get_active_player())
            except WinningCondition as e:
                print(e.message)
                is_running = False
                gui.close()


if __name__ == "__main__":
    main()