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
    rules['players'] = ['Skipper']
    rules['generator_rules']['river_rules'] = []
    game = Game(rules=rules)
    field = game.field
    gui = SpectatorGUI(field)

    state = Actions.move

    while game.is_running:
        act_pl_abilities = field.get_player_allowed_abilities(game.get_current_player())
        gui.draw(act_pl_abilities)
        act, state = gui.get_action(act_pl_abilities, state)
        if act:

            response = game.field.action_handler(*act)

            print(response.get_turn_info(), response.get_info())
            game.check_win_condition(rules)

    gui.close()


if __name__ == "__main__":
    main()