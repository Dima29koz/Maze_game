"""Base game rules"""

rules = {
    'generator_rules': {
        'rows': 4, 'cols': 5,
        'is_rect': False,
        'river_rules': [5, 3],
        'armory': True,
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
    'gameplay_rules': {'fast_win': False},
    'player_stat': {
        'max_health': 2,
        'max_arrows': 3,
        'max_bombs': 3
    }
}
