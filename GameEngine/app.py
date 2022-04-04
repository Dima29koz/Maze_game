from operator import attrgetter

from GUI.spectator import SpectatorGUI
from GameEngine.game import Game
from GameEngine.globalEnv.enums import Actions


from rules import rules

"""
Сломано! Но работает
"""


def main():
    rules['generator_rules']['river_rules'] = []
    game = Game(rules=rules)
    field = game.field
    field.spawn_player({'x': 1, 'y': 1}, 'Skipper', 1)
    # field.spawn_player({'x': 1, 'y': 1}, 'Tester', 2)
    gui = SpectatorGUI(field)

    state = Actions.move
    is_running = True
    while is_running:
        act_pl_abilities = field.get_player_allowed_abilities(game.get_current_player())
        gui.draw(act_pl_abilities)
        act, state = gui.get_action(act_pl_abilities, state)
        if act:

            response = game.field.action_handler(*act)

            print(response.get_turn_info(), response.get_info())
            if game.is_win_condition(rules):
                is_running = False

    gui.close()


if __name__ == "__main__":
    main()
