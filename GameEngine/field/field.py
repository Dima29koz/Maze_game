from functools import partial
from operator import attrgetter
from random import choice

from GameEngine.field_generator.field_generator import FieldGenerator
from GameEngine.field import response as r, cell as c
from GameEngine.entities.player import Player
from GameEngine.entities.treasure import Treasure
from GameEngine.globalEnv.enums import Actions, Directions
from GameEngine.field.cell import Cell


class Field:
    def __init__(self, rules: dict):
        self.gameplay_rules = rules['gameplay_rules']
        generator = FieldGenerator(rules['generator_rules'])
        self.field = generator.get_field()
        self.exit_cell = generator.get_exit_cell()
        self.treasures: list[Treasure] = generator.get_treasures()
        self.players: list[Player] = []
        self._active_player_idx = 0

    def spawn_bots(self, bots: list[str]):  # fixme
        players = []
        for bot in bots:
            spawn_cell = None
            while spawn_cell is None:
                spawn_cell = choice(choice(self.field))
            players.append(Player(spawn_cell, bot, True))
        return players

    def spawn_player(self, spawn_point: dict, name: str, turn):
        player = Player(self.field[spawn_point.get('y')][spawn_point.get('x')], name, turn=turn)
        if player not in self.players:
            self.players.append(player)
            return True
        return False

    def sort_players(self):
        self.players.sort(key=attrgetter('is_bot', 'turn'))
        self.players[0].is_active = True

    def get_alive_pl_amount(self) -> int:
        return len([player for player in self.players if player.is_alive])

    def get_active_player(self) -> Player:
        return self.players[self._active_player_idx]

    def get_player_allowed_abilities(self, player: Player) -> dict[Actions, bool] | None:
        if player != self.get_active_player():
            return
        is_treasures_under = True if self._treasures_on_cell(player.cell) else False
        return player.get_allowed_abilities(is_treasures_under)

    def get_treasures_on_exit(self) -> list[Treasure] | None:
        treasures = self._treasures_on_cell(self.exit_cell)
        [self.treasures.remove(treasure) for treasure in treasures]
        return treasures

    def get_players_stat(self) -> list[dict]:
        return [player.to_dict() for player in self.players]

    def get_field_list(self):
        return [[cell.to_dict() for cell in row] for row in self.field]

    def get_field_pattern_list(self):
        return [[{'x': cell.x, 'y': cell.y} if cell else None for cell in row] for row in self.field]

    def get_treasures_list(self):
        return [{'x': treasure.cell.x, 'y': treasure.cell.y, 'type': treasure.t_type.name}
                for treasure in self.treasures]

    def get_players_list(self):
        return [{'x': player.cell.x, 'y': player.cell.y, 'name': player.name}
                for player in self.players if player.is_alive]

    def action_handler(self, action: Actions, direction: Directions | None = None) -> r.RespHandler:
        action_to_handler = {
            Actions.swap_treasure: self._treasure_swap_handler,
            Actions.shoot_bow: self._shooting_handler,
            Actions.throw_bomb: self._bomb_throw_handler,
            Actions.skip: self._pass_handler,
            Actions.move: self._movement_handler,
            Actions.info: self._info_handler,
        }

        player = self.players[self._active_player_idx]

        response = action_to_handler[action](player, direction)
        response.set_info(player.cell, [treasure.t_type for treasure in self._treasures_on_cell(player.cell)])
        response.update_turn_info(player.name, action.name, direction.name if direction else '')
        return response

    def _check_players(self, current_cell: Cell) -> list[Player] | None:
        return [player for player in self.players
                if player.cell == current_cell and not player.is_active and player.is_alive]

    def _treasures_on_cell(self, cell: Cell) -> list[Treasure] | None:
        return [treasure for treasure in self.treasures if cell == treasure.cell]

    def _treasure_swap_handler(self, player: Player, direction: Directions = None):
        treasures = self._treasures_on_cell(player.cell)
        has_treasure = False
        pl_treasure = player.drop_treasure()
        if pl_treasure:
            has_treasure = True
            self.treasures.append(pl_treasure)

        player.treasure = treasures.pop(0)
        self.treasures.remove(player.treasure)
        player.treasure.cell = None
        return r.RespHandlerSwapTreasure(has_treasure)

    def _shooting_handler(self, active_player: Player, shot_direction: Directions):
        current_cell = active_player.cell
        active_player.shoot_bow()
        damaged_players = []
        while not damaged_players:
            damaged_players = self._check_players(current_cell)
            if current_cell.walls[shot_direction].weapon_collision:
                break
            current_cell = current_cell.neighbours[shot_direction]

        lost_treasure_players, dead_players = self._player_take_dmg_handler(damaged_players)
        self._pass_handler(active_player)
        return r.RespHandlerShootBow(damaged_players, dead_players, lost_treasure_players)

    def _player_take_dmg_handler(self, damaged_players: list[Player]):
        lost_treasure_players = []
        dead_players = []
        for player in damaged_players:

            treasure = player.take_damage()
            if not player.is_alive:
                dead_players.append(player)

            if treasure:
                lost_treasure_players.append(player)
                self.treasures.append(treasure)
        return lost_treasure_players, dead_players

    def _bomb_throw_handler(self, active_player: Player, throwing_direction: Directions):
        active_player.throw_bomb()
        wall = active_player.cell.break_wall(throwing_direction)
        self._pass_handler(active_player)
        return r.RespHandlerBombing(wall)

    def _pass_handler(self, active_player: Player, direction: Directions = None):
        new_pl_cell = active_player.cell.idle(active_player.cell)
        active_player.move(new_pl_cell)
        self._cell_mechanics_activator(active_player, new_pl_cell)
        self._pass_turn_to_next_player()
        return r.RespHandlerSkip()

    def _movement_handler(self, active_player: Player, movement_direction: Directions):
        current_cell = active_player.cell
        pl_collision, pl_state, wall_type = current_cell.check_wall(movement_direction)
        cell = current_cell.neighbours[movement_direction] if not pl_collision else current_cell
        new_pl_cell = cell.active(current_cell) if pl_state else cell.idle(current_cell)
        active_player.move(new_pl_cell)
        self._cell_mechanics_activator(active_player, new_pl_cell)

        self._pass_turn_to_next_player()
        return r.RespHandlerMoving(wall_type, cell)

    def _info_handler(self, active_player: Player, movement_direction: Directions):
        self._pass_turn_to_next_player()
        return r.RespHandlerInfo()

    def _cell_mechanics_activator(self, player: Player, cell):
        cell_type_to_player_handler = {
            c.CellExit: partial(self._update_treasures_exit, player),
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

    def _update_treasures_exit(self, player):
        treasure = player.drop_treasure()
        if treasure:
            self.treasures.append(treasure)
