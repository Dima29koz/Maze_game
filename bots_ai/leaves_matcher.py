from typing import Type

from GameEngine.field import cell
from bots_ai.field_obj import UnknownCell
from bots_ai.field_state import FieldState


class LeavesMatcher:
    def __init__(self,
                 unique_objs_amount: dict[Type[cell.Cell], int],
                 players_roots: dict[str, FieldState]):
        self.unique_objs_amount = unique_objs_amount
        self.players_roots = players_roots

    def match_leaves(self, player_name: str):
        active_player_nodes = self.get_player_leaves(player_name)[::-1]
        other_players = list(self.players_roots.keys())
        other_players.remove(player_name)
        if not other_players:
            return

        for node in active_player_nodes:
            if not self._match_node(node.field, other_players):
                if node.is_real:
                    for row in node.field:
                        print(row)
                node.remove()

    def get_player_leaves(self, player_name: str) -> list[FieldState]:
        return self.players_roots.get(player_name).get_leaf_nodes()

    def _match_node(self, field: list[list[cell.Cell | cell.CellRiver | None]], other_players: list[str]):
        for player in other_players:
            matchable_with_player_nodes = False
            for pl_node in self.get_player_leaves(player)[::-1]:
                if self.is_matchable(field, pl_node.field):
                    matchable_with_player_nodes = True
                    break
            if not matchable_with_player_nodes:
                return False
        return True

    def is_matchable(self, field: list[list[cell.Cell | cell.CellRiver | None]],
                     other_field: list[list[cell.Cell | cell.CellRiver | None]]):
        unique_objs = self.unique_objs_amount
        for y, row in enumerate(field):
            for x, self_cell in enumerate(row):
                other_cell = other_field[y][x]
                if self_cell is None and other_cell is None:
                    continue
                if other_cell is None and type(self_cell) is cell.CellExit:
                    continue
                if self_cell is None and type(other_cell) is cell.CellExit:
                    continue

                if type(other_cell) is UnknownCell:
                    if unique_objs.get(type(self_cell)) is not None:
                        if unique_objs.get(type(self_cell)) > 0:
                            unique_objs[type(self_cell)] -= 1
                        else:
                            return False
                    continue
                if type(self_cell) is UnknownCell:
                    if unique_objs.get(type(other_cell)) is not None:
                        if unique_objs.get(type(other_cell)) > 0:
                            unique_objs[type(other_cell)] -= 1
                        else:
                            return False
                    continue

                if type(other_cell) is type(self_cell):
                    if unique_objs.get(type(self_cell)) is not None:
                        if unique_objs.get(type(self_cell)) > 0:
                            unique_objs[type(self_cell)] -= 1
                        else:
                            return False
                    if type(other_cell) is cell.CellRiver:
                        if other_cell.direction is not self_cell.direction:
                            return False
                    continue
                else:
                    return False
        return True
