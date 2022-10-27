"""Base game rules"""

rules = {
    'generator_rules': {
        'seed': 0,
        'rows': 5, 'cols': 5,
        'dimensions_amount': 1,
        'levels_amount': 1,
        'exits_amount': 2,
        'is_not_rect': False,
        'is_separated_armory': False,
        'river_rules': {
            'has_river': True,
            'has_fort': False,
            'min_coverage': 30,
            'max_coverage': 70,
            'min_len': 2,
        },
        'treasures': [1, 1, 0],
        'walls': {
            'has_walls': True,
            'concrete': True,
            'rubber': False,
        }
    },
    'host_rules': {},
    'players_amount': 2,
    'bots_amount': 0,
    'gameplay_rules': {
        'fast_win': True,  # player wins if he is the only survivor
        'diff_outer_concrete_walls': False,  # if true you won't know difference between WallConcrete and WallOuter
    },
    'player_stat': {
        'max_health': 2,
        'max_arrows': 3,
        'max_bombs': 3
    }
}
