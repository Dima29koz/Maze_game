from game_engine.global_env.enums import Actions


class PlayerStats:
    def __init__(self, game_rules: dict):
        self.health_max = game_rules.get('player_stat').get('max_health')
        self.health = self.health_max
        self.bombs_max = game_rules.get('player_stat').get('max_bombs')
        self.bombs = self.bombs_max
        self.arrows_max = game_rules.get('player_stat').get('max_arrows')
        self.arrows = self.arrows_max
        self.has_treasure: bool = False
        self.is_alive = True

    def get_allowed_abilities(self) -> dict[Actions, bool]:
        """returns dict of player abilities"""
        return {
            Actions.move: True,
            Actions.shoot_bow: True if self.arrows > 0 else False,
            Actions.throw_bomb: True if self.bombs > 0 else False,
            Actions.swap_treasure: True if self.health == self.health_max else False,
            Actions.skip: True,
            Actions.info: True,
        }

    def restore_heal(self):
        self.health = self.health_max

    def restore_bombs(self):
        self.bombs = self.bombs_max

    def restore_arrows(self):
        self.arrows = self.arrows_max

    def restore_weapon(self):
        self.restore_bombs()
        self.restore_arrows()

    def on_shooting(self):
        self.arrows -= 1

    def on_bombing(self):
        self.bombs -= 1

    def on_swap_treasure(self):
        if not self.has_treasure:
            self.has_treasure = True
            return True
        return False

    def on_take_dmg(self):
        self.health -= 1
        if self.health == 0:
            self.is_alive = False
        if self.has_treasure and self.health <= self.health_max // 2:
            self.has_treasure = False
