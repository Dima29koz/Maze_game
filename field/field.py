from typing import Optional

from field_generator.field_generator import FieldGenerator
from field.host import Host
from globalEnv.Exepts import WinningCondition, PlayerDeath
from entities.player import Player
from entities.treasure import Treasure
from globalEnv.enums import Actions, Directions, TreasureTypes
from field.cell import *


class Field:
    def __init__(self, rules: dict):
        field = FieldGenerator(rules['generator_rules'])
        self.host = Host(rules['host_rules'])
        self.field = field.get_field()
        self.treasures: list[Treasure] = field.get_treasures()
        self.players = self.spawn_players()
        self.dead_players: list[Player] = []
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

    def spawn_players(self, rules=None):
        players = []
        players.append(Player(self.field[1][1], 'skipper'))
        players[0].is_active = True
        players.append(Player(self.field[1][0], 'tester'))
        return players

    def get_players(self):
        return self.players

    def action_handler(self, action: Actions, direction: Optional[Directions] = None):
        player = self.players[self.active_player]
        try:
            response = self.action_to_handler[action](player, direction)
        except WinningCondition:
            raise WinningCondition(f'{player.name} WIN')
        except KeyError:
            response = {}
            print('что-то пошло не так, не ожидаемое действие', action)

        treasures = self.treasures_on_cell(player.cell)
        if treasures:
            response['info'].append(f'клад ({len(treasures)}шт)')

        res = {
            'player': player.name,
            'action': action.name,
            'direction': direction.name if direction else None,
            'response': response
        }

        self.host.give_info(res)

    def check_players(self, current_cell, active_player) -> list[Player]:
        current_players = []
        for player in self.players:
            if player.cell == current_cell and player is not active_player:
                current_players.append(player)
        return current_players

    def swap_treasure(self, treasures: list[Treasure], player: Player):
        pl_treasure = player.drop_treasure()
        if pl_treasure:
            pl_treasure.cell = player.cell
            self.treasures.append(pl_treasure)

        player.treasure = treasures.pop(0)
        self.treasures.remove(player.treasure)
        player.treasure.cell = None

    def treasures_on_cell(self, cell):
        treasures = []
        for treasure in self.treasures:
            if cell == treasure.cell:
                treasures.append(treasure)
        return treasures

    def treasure_swap_handler(self, active_player, direction=None):
        response = {'info': ['на клетке игрока нет клада']}
        if active_player.can_take_treasure():
            treasures = self.treasures_on_cell(active_player.cell)
            if treasures:
                self.swap_treasure(treasures, active_player)
                response['info'] = ['игрок сменил клад']
            return response
        else:
            response['info'] = ['только полностью здоровые игроки могут поднять клад']
            return response

    def shooting_handler(self, active_player, shot_direction):
        response = {
            'info': ['не попал'],  # 'не попал'/'попал'/'нет стрел'
            'damaged_players': [],  # список раненых игроков
            'lost_treasure_players': []  # список игроков, потерявших клад
        }
        if active_player.shoot_bow():
            current_cell = active_player.cell
            current_players = self.check_players(current_cell, active_player)
            while not current_players:
                if current_cell.walls[shot_direction].weapon_collision:
                    break
                current_cell = current_cell.neighbours[shot_direction]
                current_players = self.check_players(current_cell, active_player)
            else:
                response['info'] = ['попал']
                response['damaged_players'] = [player.name for player in current_players]
                pl_dr = []
                for player in current_players:
                    try:
                        treasure = player.dropped_treasure()
                    except PlayerDeath:
                        print(player.name, 'убит')  # todo добавить обработчик зависящий от правил игры
                        self.players.remove(player)
                        self.dead_players.append(player)
                        if len(self.players) == 1:
                            raise WinningCondition
                    else:
                        if treasure:
                            pl_dr.append(player.name)
                            self.treasures.append(treasure)
                response['lost_treasure_players'] = pl_dr
            response['info'].extend(self.pass_handler(active_player)['info'])
            return response
        else:
            response['info'] = ['нет стрел']
            return response

    def bomb_throw_handler(self, active_player, throwing_direction):
        response = {'info': ['нет бомб']}
        if active_player.throw_bomb():
            if active_player.cell.break_wall(throwing_direction):
                response['info'] = ['взорвал']
            else:
                response['info'] = ['не взорвал']
            response['info'].extend(self.pass_handler(active_player)['info'])
        return response

    def pass_handler(self, active_player: Player, direction=None) -> dict:
        new_pl_cell = active_player.cell.idle(active_player.cell)
        active_player.move(new_pl_cell)
        self.cell_mechanics_activator(active_player, new_pl_cell)
        self.pass_the_turn_to_the_next_player()
        return {'info': [type(new_pl_cell)]}

    def movement_handler(self, active_player: Player, movement_direction) -> dict:
        current_cell = active_player.cell
        pl_collision, pl_state, wall_type = current_cell.check_wall(movement_direction)
        cell = current_cell.neighbours[movement_direction] if not pl_collision else current_cell
        new_pl_cell = cell.active(current_cell) if pl_state else cell.idle(current_cell)
        active_player.move(new_pl_cell)
        self.cell_mechanics_activator(active_player, new_pl_cell)

        self.pass_the_turn_to_the_next_player()
        return {'info': [type(new_pl_cell)]}

    @staticmethod
    def cell_mechanics_activator(player: Player, cell):
        cell_type_to_player_handler = {
            CellExit: player.came_out_maze,
            CellClinic: player.heal,
            CellArmory: player.restore_armory,
            CellArmoryWeapon: player.restore_arrows,
            CellArmoryExplosive: player.restore_bombs,
        }
        if type(cell) in cell_type_to_player_handler.keys():
            try:
                cell_type_to_player_handler[type(cell)]()
            except WinningCondition:
                raise

    def pass_the_turn_to_the_next_player(self):
        self.players[self.active_player].is_active = False
        self.active_player = (self.active_player + 1) % len(self.players)
        self.players[self.active_player].is_active = True
        if self.active_player + 1 == len(self.players):
            self.host_turn()

    def host_turn(self):
        for treasure in self.treasures:
            treasure.idle()

    def player_turn_start_handler(self):
        player = self.players[self.active_player]
        player.abilities[Actions.shoot_bow] = True if player.arrows > 0 else False
        player.abilities[Actions.throw_bomb] = True if player.bombs > 0 else False
        player.abilities[Actions.swap_treasure] = True if player.can_take_treasure() and self.treasures_on_cell(
            player.cell) else False
        return self.players[self.active_player].get_allowed_abilities()

    def player_turn_end_handler(self):
        pass
