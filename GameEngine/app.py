"""runs game local for testing GameEngine"""

from GUI.spectator import SpectatorGUI
from GameEngine.game import Game
from GameEngine.globalEnv.enums import Actions

from GameEngine.rules import rules
from bots_ai.core import BotAI


def main():
    # rules['generator_rules']['river_rules']['has_river'] = False
    # rules['generator_rules']['walls']['has_walls'] = False
    # rules['generator_rules']['exits_amount'] = 20
    rules['generator_rules']['is_separated_armory'] = True
    rules['generator_rules']['seed'] = 0.2887757181832208
    rules['gameplay_rules']['fast_win'] = False
    rules['gameplay_rules']['diff_outer_concrete_walls'] = True
    # rules['generator_rules']['river_rules']['min_coverage'] = 90
    # rules['generator_rules']['river_rules']['max_coverage'] = 100
    spawn: dict[str, int] = {'x': 3, 'y': 1}
    spawn2: dict[str, int] = {'x': 1, 'y': 4}

    players = [
        (spawn, 'Skipper'),
        (spawn2, 'Tester'),
    ]

    bot = None

    game = Game(rules=rules)
    field = game.field
    for i, player in enumerate(players, 1):
        field.spawn_player(*player, turn=i)

    bot = BotAI(rules, players)
    bot.real_field = field.field
    gui = SpectatorGUI(field, bot)

    state = Actions.move
    is_running = True

    for _ in players:
        response = game.field.action_handler(Actions.info)
        print(response.get_turn_info(), response.get_info())
        bot.process_turn_resp(response.get_raw_info())
        bot.turn_prepare(game.get_current_player().name)

    while is_running:
        act_pl_abilities = field.get_player_allowed_abilities(game.get_current_player())
        gui.draw(act_pl_abilities, game.get_current_player().name)
        act, state = gui.get_action(act_pl_abilities, state)
        if act:
            response = game.field.action_handler(*act)
            print(response.get_turn_info(), response.get_info())
            player_name = response.get_turn_info().get('player_name')
            # print(response.get_raw_info().get('response'))
            bot.process_turn_resp(response.get_raw_info())
            print('spawns: ', bot.get_spawn_amount(player_name))
            # print('Has bad nodes - ', bot.has_bad_nodes(player_name))
            if game.is_win_condition(rules):
                is_running = False
            bot.turn_prepare(game.get_current_player().name)
    gui.close()


if __name__ == "__main__":
    main()
