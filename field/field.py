from typing import Optional

from field_generator.field_generator import FieldGenerator
import field.response as r
from globalEnv.Exceptions import WinningCondition, PlayerDeath
from entities.player import Player
from entities.treasure import Treasure
from globalEnv.enums import Actions, Directions, TreasureTypes
from field.cell import Cell
import field.cell as c


class Field:
    def __init__(self, rules: dict):
        self.gameplay_rules = rules['gameplay_rules']
        generator = FieldGenerator(rules['generator_rules'])
        self.field = generator.get_field()
        self.treasures: list[Treasure] = generator.get_treasures()
        self.players: list[Player] = self.spawn_players(rules['players'])
        self.active_player = 0

        self.action_to_handler = {
            Actions.swap_treasure: self.treasure_swap_handler,
            Actions.shoot_bow: self.shooting_handler,
            Actions.throw_bomb: self.bomb_throw_handler,
            Actions.skip: self.pass_handler,
            Actions.move: self.movement_handler,
        }

    def get_field(self):
        return self.field

    def get_treasures(self):
        return self.treasures

    def spawn_players(self, players_: list[str]):
        players = []
        for player in players_:
            players.append(Player(self.field[1][1], player))
        players[0].is_active = True
        return players

    def get_players(self):
        return self.players

    def action_handler(self, action: Actions, direction: Optional[Directions] = None) -> r.RespHandler:
        player = self.players[self.active_player]
        try:
            response = self.action_to_handler[action](player, direction)
            response.update_treasure_info(len(self.treasures_on_cell(player.cell)))
            response.update_turn_info(player.name, action.name, direction.name if direction else '')
            return response
        except WinningCondition:
            raise WinningCondition(f'{player.name} WIN')
        except KeyError:
            print('что-то пошло не так, не ожидаемое действие', action)

    def check_players(self, current_cell: Cell) -> list[Player]:
        current_players = []
        for player in self.players:
            if player.cell == current_cell and not player.is_active and player.is_alive:
                current_players.append(player)
        return current_players

    def treasures_on_cell(self, cell: Cell):
        treasures = []
        for treasure in self.treasures:
            if cell == treasure.cell:
                treasures.append(treasure)
        return treasures

    def treasure_swap_handler(self, player: Player, direction: Directions = None):
        treasures = self.treasures_on_cell(player.cell)
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

    def shooting_handler(self, active_player: Player, shot_direction: Directions):
        hit = False
        lost_treasure_players = []
        dead_players = []
        current_cell = active_player.cell
        active_player.shoot_bow()
        damaged_players = self.check_players(current_cell)
        while not damaged_players:
            if current_cell.walls[shot_direction].weapon_collision:
                break
            current_cell = current_cell.neighbours[shot_direction]
            damaged_players = self.check_players(current_cell)
        else:
            hit = True
            lost_treasure_players, dead_players = self.player_take_dmg_handler(damaged_players)

        new_pl_location = self.pass_handler(active_player).new_location
        return r.RespHandlerShootBow(hit, damaged_players, dead_players, lost_treasure_players, new_pl_location)

    def player_take_dmg_handler(self, damaged_players: list[Player]):
        lost_treasure_players = []
        dead_players = []
        for player in damaged_players:
            try:
                treasure = player.dropped_treasure()
            except PlayerDeath:  # todo добавить обработчик зависящий от правил игры
                dead_players.append(player)
                if self.alive_pl_amount() == 1 and self.gameplay_rules['fast_win']:
                    raise WinningCondition
            else:
                if treasure:
                    lost_treasure_players.append(player)
                    self.treasures.append(treasure)
        return lost_treasure_players, dead_players

    def alive_pl_amount(self):
        amount = 0
        for player in self.players:
            if player.is_alive:
                amount += 1
        return amount

    def bomb_throw_handler(self, active_player: Player, throwing_direction: Directions):
        active_player.throw_bomb()
        wall = active_player.cell.break_wall(throwing_direction)
        new_pl_location = self.pass_handler(active_player).new_location
        return r.RespHandlerBombing(wall, new_pl_location)

    def pass_handler(self, active_player: Player, direction: Directions = None):
        new_pl_cell = active_player.cell.idle(active_player.cell)
        active_player.move(new_pl_cell)
        self.cell_mechanics_activator(active_player, new_pl_cell)
        self.pass_the_turn_to_the_next_player()
        return r.RespHandlerSkip(type(new_pl_cell))

    def movement_handler(self, active_player: Player, movement_direction: Directions):
        current_cell = active_player.cell
        pl_collision, pl_state, wall_type = current_cell.check_wall(movement_direction)
        cell = current_cell.neighbours[movement_direction] if not pl_collision else current_cell
        new_pl_cell = cell.active(current_cell) if pl_state else cell.idle(current_cell)
        active_player.move(new_pl_cell)
        self.cell_mechanics_activator(active_player, new_pl_cell)

        self.pass_the_turn_to_the_next_player()
        return r.RespHandlerMoving(wall_type, cell, new_pl_cell)

    @staticmethod
    def cell_mechanics_activator(player: Player, cell):
        cell_type_to_player_handler = {
            c.CellExit: player.came_out_maze,
            c.CellClinic: player.heal,
            c.CellArmory: player.restore_armory,
            c.CellArmoryWeapon: player.restore_arrows,
            c.CellArmoryExplosive: player.restore_bombs,
        }
        if type(cell) in cell_type_to_player_handler.keys():
            cell_type_to_player_handler[type(cell)]()

    def pass_the_turn_to_the_next_player(self):
        self.players[self.active_player].is_active = False
        self.active_player = (self.active_player + 1) % len(self.players)
        self.players[self.active_player].is_active = True
        if self.active_player + 1 == len(self.players):
            self.host_turn()
        if not self.players[self.active_player].is_alive:
            self.pass_the_turn_to_the_next_player()

    def host_turn(self):
        for treasure in self.treasures:
            treasure.idle()

    def player_turn_start_handler(self):
        """
        :return: active player allowed_abilities
        """
        player = self.players[self.active_player]
        is_treasures_under = True if self.treasures_on_cell(player.cell) else False
        return player.get_allowed_abilities(is_treasures_under)
