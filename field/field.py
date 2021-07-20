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
        self.players.append(Player(self.field[1][1]))
        # self.players.append(Player(self.field[1][0]))

    def get_players(self):
        return self.players

    def check_treasure(self):
        """
        :return: сокровища под игроком
        """
        player = self.players[self.active_player]
        treasures = []
        for treasure in self.treasures:
            if player.cell == treasure.cell:
                treasures.append(treasure)
        return treasures

    def check_players(self, cell, active_player) -> list[Player]:
        """
        :return: список игроков на данной клетке
        """
        current_players = []
        for player in self.players:
            if player.cell == cell and player is not active_player:
                current_players.append(player)
        return current_players

    def swap_treasure(self, treasures: list[Treasure]):
        player = self.players[self.active_player]
        if player.treasure:
            player.treasure.cell = player.cell
            self.treasures.append(player.treasure)
            player.treasure = None

        player.treasure = treasures.pop(0)
        self.treasures.remove(player.treasure)
        player.treasure.cell = None

    def action_handler(self, action: Actions, direction: Directions):
        host_turn = False
        player = self.players[self.active_player]
        if action is Actions.swap_treasure:
            if player.can_take_treasure():
                treasures = self.check_treasure()
                if treasures:
                    self.swap_treasure(treasures)
        elif action is Actions.hurted:
            if player.was_hit():
                player.treasure.cell = player.cell
                self.treasures.append(player.drop_treasure())
        elif action is Actions.shoot_bow:
            if player.shoot_bow():
                current_cell = player.cell
                current_players = self.check_players(current_cell, player)
                while not current_players:
                    if current_cell.walls[direction].weapon_collision:
                        break
                    current_cell = current_cell.neighbours[direction]
                    current_players = self.check_players(current_cell, player)
                else:
                    for other_player in current_players:
                        if other_player.was_hit():
                            other_player.treasure.cell = other_player.cell
                            self.treasures.append(other_player.drop_treasure())

            self.active_player = (self.active_player + 1) % len(self.players)
            if self.active_player + 1 == len(self.players):
                host_turn = True
        else:
            if player.action(action, direction):
                self.active_player = (self.active_player + 1) % len(self.players)
                if self.active_player + 1 == len(self.players):
                    host_turn = True
        if host_turn:
            for treasure in self.treasures:
                treasure.idle()
