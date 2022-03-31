from GameEngine.field_generator.field_generator import FieldGenerator
from GameEngine.field import response as r, cell as c
from GameEngine.globalEnv.Exceptions import WinningCondition, PlayerDeath
from GameEngine.entities.player import Player
from GameEngine.entities.treasure import Treasure
from GameEngine.globalEnv.enums import Actions, Directions
from GameEngine.field.cell import Cell


class Field:
    def __init__(self, rules: dict):
        self.gameplay_rules = rules['gameplay_rules']
        generator = FieldGenerator(rules['generator_rules'])
        self.field = generator.get_field()
        self.treasures: list[Treasure] = generator.get_treasures()
        self.players: list[Player] = []
        self._active_player_idx = 0

    def spawn_players(self, players_: list[str], bots_: list[str]):  # fixme
        players = []
        for player in players_:
            players.append(Player(self.field[1][1], player))
        for bot in bots_:
            players.append(Player(self.field[1][1], bot, True))
        players[0].is_active = True
        return players

    def get_alive_pl_amount(self) -> int:
        return len([player for player in self.players if player.is_alive])

    def get_active_player(self) -> Player:
        return self.players[self._active_player_idx]

    def get_player_allowed_abilities(self, player: Player) -> dict[Actions, bool] | None:
        if player != self.get_active_player():
            return
        is_treasures_under = True if self._treasures_on_cell(player.cell) else False
        return player.get_allowed_abilities(is_treasures_under)

    def get_players_stat(self) -> list[dict]:
        return [player.to_dict() for player in self.players]

    def action_handler(self, action: Actions, direction: Directions | None = None) -> r.RespHandler:
        action_to_handler = {
            Actions.swap_treasure: self._treasure_swap_handler,
            Actions.shoot_bow: self._shooting_handler,
            Actions.throw_bomb: self._bomb_throw_handler,
            Actions.skip: self._pass_handler,
            Actions.move: self._movement_handler,
        }

        player = self.players[self._active_player_idx]
        try:
            response = action_to_handler[action](player, direction)
            response.update_cell_info(len(self._treasures_on_cell(player.cell)), type(player.cell))
            response.update_turn_info(player.name, action.name, direction.name if direction else '')
            return response
        except WinningCondition:  # fixme
            raise WinningCondition(f'{player.name} WIN')
        except KeyError:
            print('что-то пошло не так, не ожидаемое действие', action)

    def _check_players(self, current_cell: Cell) -> list[Player]:
        return [player for player in self.players
                if player.cell == current_cell and not player.is_active and player.is_alive]

    def _treasures_on_cell(self, cell: Cell) -> list[Treasure]:
        return [treasure for treasure in self.treasures if cell == treasure.cell]

    def _treasure_swap_handler(self, player: Player, direction: Directions = None):
        treasures = self._treasures_on_cell(player.cell)
        has_treasure = False
        pl_treasure = player.drop_treasure()
        if pl_treasure:
            has_treasure = True
            pl_treasure.cell = player.cell
            self.treasures.append(pl_treasure)

        player.treasure = treasures.pop(0)
        self.treasures.remove(player.treasure)
        player.treasure.cell = None
        return r.RespHandlerSwapTreasure(has_treasure)

    def _shooting_handler(self, active_player: Player, shot_direction: Directions):
        hit = False
        lost_treasure_players = []
        dead_players = []
        current_cell = active_player.cell
        active_player.shoot_bow()
        damaged_players = []
        while not damaged_players:
            damaged_players = self._check_players(current_cell)
            if current_cell.walls[shot_direction].weapon_collision:
                break
            current_cell = current_cell.neighbours[shot_direction]
        else:
            hit = True
            lost_treasure_players, dead_players = self._player_take_dmg_handler(damaged_players)

        new_pl_location = self._pass_handler(active_player).new_location
        return r.RespHandlerShootBow(hit, damaged_players, dead_players, lost_treasure_players, new_pl_location)

    def _player_take_dmg_handler(self, damaged_players: list[Player]):
        lost_treasure_players = []
        dead_players = []
        for player in damaged_players:
            try:
                treasure = player.take_damage()

            except PlayerDeath:  # todo добавить обработчик зависящий от правил игры
                dead_players.append(player)
                if self.get_alive_pl_amount() == 1 and self.gameplay_rules['fast_win']:
                    raise WinningCondition
            else:
                if treasure:
                    treasure.cell = player.cell
                    lost_treasure_players.append(player)
                    self.treasures.append(treasure)
        return lost_treasure_players, dead_players

    def _bomb_throw_handler(self, active_player: Player, throwing_direction: Directions):
        active_player.throw_bomb()
        wall = active_player.cell.break_wall(throwing_direction)
        new_pl_location = self._pass_handler(active_player).new_location
        return r.RespHandlerBombing(wall, new_pl_location)

    def _pass_handler(self, active_player: Player, direction: Directions = None):
        new_pl_cell = active_player.cell.idle(active_player.cell)
        active_player.move(new_pl_cell)
        self._cell_mechanics_activator(active_player, new_pl_cell)
        self._pass_turn_to_next_player()
        return r.RespHandlerSkip(type(new_pl_cell))

    def _movement_handler(self, active_player: Player, movement_direction: Directions):
        current_cell = active_player.cell
        pl_collision, pl_state, wall_type = current_cell.check_wall(movement_direction)
        cell = current_cell.neighbours[movement_direction] if not pl_collision else current_cell
        new_pl_cell = cell.active(current_cell) if pl_state else cell.idle(current_cell)
        active_player.move(new_pl_cell)
        self._cell_mechanics_activator(active_player, new_pl_cell)

        self._pass_turn_to_next_player()
        return r.RespHandlerMoving(wall_type, cell, new_pl_cell)

    @staticmethod
    def _cell_mechanics_activator(player: Player, cell):
        cell_type_to_player_handler = {
            c.CellExit: player.came_out_maze,
            c.CellClinic: player.heal,
            c.CellArmory: player.restore_armory,
            c.CellArmoryWeapon: player.restore_arrows,
            c.CellArmoryExplosive: player.restore_bombs,
        }
        if type(cell) in cell_type_to_player_handler.keys():
            cell_type_to_player_handler[type(cell)]()

    def _pass_turn_to_next_player(self):
        self.players[self._active_player_idx].is_active = False
        self._active_player_idx = (self._active_player_idx + 1) % len(self.players)
        self.players[self._active_player_idx].is_active = True
        if self._active_player_idx + 1 == len(self.players):
            self._host_turn()
        if not self.players[self._active_player_idx].is_alive:
            self._pass_turn_to_next_player()

    def _host_turn(self):
        for treasure in self.treasures:
            treasure.idle()
