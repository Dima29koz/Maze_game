from copy import copy
from typing import Type

from GameEngine.field import cell
from bots_ai.field_obj import UnknownCell
from bots_ai.field_state import FieldState


class InitGenerator:
    def __init__(self, game_rules: dict, players: list[str]):
        self._rules = game_rules
        self._players = players
        self._size_x: int = game_rules.get('generator_rules').get('cols')
        self._size_y: int = game_rules.get('generator_rules').get('rows')
        self._cols = self._size_x + 2
        self._rows = self._size_y + 2
        self._unique_objs = self._gen_field_objs_amount()
        self._spawn_points = self._gen_spawn_points()

    def get_start_state(self, player):
        other_players = copy(self._players)
        other_players.remove(player[1])
        field = self._generate_start_field()
        root_state = FieldState(
            field, self.get_unique_obj_amount(),
            {player_name: True for player_name in other_players})
        real_spawn = (player[0].get('x'), player[0].get('y'))
        for point in self._spawn_points:
            next_state = root_state.copy(*point)
            if point == real_spawn:
                next_state.is_real_spawn = True
            root_state.next_states.append(next_state)
        return root_state

    def get_unique_obj_amount(self) -> dict[Type[cell.Cell], int]:
        return self._unique_objs.copy()

    def _gen_field_objs_amount(self) -> dict[Type[cell.Cell], int]:
        obj_amount = {
            cell.CellClinic: 1,
        }
        if self._rules.get('generator_rules').get('is_separated_armory'):
            obj_amount.update({
                cell.CellArmoryWeapon: 1,
                cell.CellArmoryExplosive: 1,
            })
        else:
            obj_amount.update({
                cell.CellArmory: 1,
            })
        return obj_amount

    def _gen_spawn_points(self):
        xr = range(1, self._size_x + 1)
        yr = range(1, self._size_y + 1)
        return [(x, y) for y in yr for x in xr]

    def _generate_start_field(self):
        none_cols = [0, self._cols - 1]
        none_rows = [0, self._rows - 1]

        field = [[UnknownCell(col, row)
                  if row not in none_rows and col not in none_cols else None
                  for col in range(self._cols)] for row in range(self._rows)]
        return field
