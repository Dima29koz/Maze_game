from typing import Optional

from field_generator.field_generator import FieldGenerator
from entities.player import Player
from entities.treasure import Treasure
from enums import Actions, Directions


class Field:
    def __init__(self):
        field = FieldGenerator(5, 4)
        self.field = field.get_field()
        self.treasures: list[Treasure] = field.get_treasures()
        self.players: list[Player] = []
        self.spawn_players()
        self.active_player = 0

    def get_field(self):
        return self.field

    def get_treasures(self):
        return self.treasures

    def spawn_players(self):
        self.players.append(Player(self.field[1][1], 'player1'))
        # self.players.append(Player(self.field[1][0], 'player2'))

    def get_players(self):
        return self.players

    def action_handler(self, act):
        player = self.players[self.active_player]
        action: Actions = act[0]
        direction: Optional[Directions] = act[1]

        if action is Actions.swap_treasure:
            response = self.treasure_pickup_handler(player)
        elif action is Actions.shoot_bow:  # todo не работает механика idle, так и должно быть?, нет не должно
            response = self.shooting_handler(player, direction)
        elif action is Actions.throw_bomb:  # todo не работает механика idle, так и должно быть?, нет не должно
            response = self.bomb_throw_handler(player, direction)
        elif action is Actions.skip:  # todo должно ли вообще хоть что-то сообщаться? - да должно всегда
            response = self.idle_handler(player)
        elif action is Actions.move:  # todo
            response = self.movement_handler(player, direction)
        else:
            response = {}
            print('!!!!', action)

        res = {
            'player': player.name,
            'action': action.name,
            'direction': direction.name if direction else None,
            'response': response
        }
        print(res)

    def check_players(self, current_cell, active_player) -> list[Player]:
        current_players = []
        for player in self.players:
            if player.cell == current_cell and player is not active_player:
                current_players.append(player)
        return current_players

    def swap_treasure(self, treasures: list[Treasure], player):
        if player.treasure:
            player.treasure.cell = player.cell
            self.treasures.append(player.treasure)
            player.treasure = None

        player.treasure = treasures.pop(0)
        self.treasures.remove(player.treasure)
        player.treasure.cell = None

    def treasure_pickup_handler(self, active_player):
        response = {'info': 'на клетке игрока нет клада'}
        if active_player.can_take_treasure():
            treasures = []
            for treasure in self.treasures:
                if active_player.cell == treasure.cell:
                    treasures.append(treasure)
            if treasures:
                self.swap_treasure(treasures, active_player)
                response['info'] = 'игрок сменил клад'
            return response
        else:
            response['info'] = 'только полностью здоровые игроки могут поднять клад'
            return response

    def shooting_handler(self, active_player, shot_direction):
        response = {
            'info': 'не попал',  # 'не попал'/'попал'/'нет стрел'
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
                response['info'] = 'попал'
                response['damaged_players'] = [player.name for player in current_players]
                pl_dr = []
                for player in current_players:
                    treasure = player.dropped_treasure()  # todo игрока невозможно убить
                    if treasure:
                        pl_dr.append(player.name)
                        self.treasures.append(treasure)
                response['lost_treasure_players'] = pl_dr
            # active_player.
            self.pass_the_turn_to_the_next_player()
            return response
        else:
            response['info'] = 'нет стрел'
            return response

    def bomb_throw_handler(self, active_player, throwing_direction):
        response = {'info': 'у игрока кочились бомбы, сделай другой ход'}
        if active_player.throw_bomb():
            if active_player.cell.break_wall(throwing_direction):
                response['info'] = 'взорвал'
            else:
                response['info'] = 'не взорвал'
            self.pass_the_turn_to_the_next_player()
            return response
        else:
            return response

    def idle_handler(self, active_player):
        response = active_player.cell.idle(active_player)
        self.pass_the_turn_to_the_next_player()
        return response

    def movement_handler(self, active_player, movement_direction):
        response = active_player.cell.check_wall(active_player, movement_direction)
        self.pass_the_turn_to_the_next_player()
        return response

    def pass_the_turn_to_the_next_player(self):
        self.active_player = (self.active_player + 1) % len(self.players)
        if self.active_player + 1 == len(self.players):
            self.host_turn()

    def host_turn(self):
        for treasure in self.treasures:
            treasure.idle()