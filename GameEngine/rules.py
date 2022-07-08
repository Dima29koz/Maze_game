"""Base game rules"""

rules = {
    'generator_rules': {
        'rows': 5, 'cols': 5,
        'exits_amount': 2,
        'is_rect': True,
        'is_separated_armory': False,
        'river_rules': {
            'has_river': True,
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
    'gameplay_rules': {'fast_win': True},
    'player_stat': {
        'max_health': 2,
        'max_arrows': 3,
        'max_bombs': 3
    }
}
