from typing import Type

from GameEngine.field import cell
from GameEngine.field.cell import CellRiver, NoneCell
from GameEngine.globalEnv.enums import Actions, Directions
from GameEngine.globalEnv.types import Position
from bots_ai.field_handler.field_state import FieldState
from bots_ai.rules_preprocessor import RulesPreprocessor


class PlayerState:
    def __init__(self, start_state: FieldState, preprocessed_rules: RulesPreprocessor, name: str):
        self.root = start_state
        self.preprocessed_rules = preprocessed_rules
        self.name = name
        self.stats = self.preprocessed_rules.get_player_stats()

    def process_turn(self, player_name: str, action: Actions, direction: Directions | None, response: dict):
        # before turn processing:
        # делать ход во всех своих листах, которые противники считают возможными,
        # то есть хотя бы 1 противник думает что данный лист возможен
        # и во всех листах с настоящим спавном

        self._handle_stats_changes(player_name, action, response)
        for node in self.get_leaf_nodes()[::-1]:
            if node.check_compatibility():
                node.process_action(player_name, action, direction, response)

    def _handle_stats_changes(self, player_name: str, action: Actions, response: dict):
        if player_name == self.name:
            type_cell_turn_end: Type[cell.CELL] | None = response.get('type_cell_at_end_of_turn')

            match action:
                case Actions.shoot_bow:
                    self.stats.on_shooting()
                case Actions.throw_bomb:
                    self.stats.on_bombing()
                case Actions.swap_treasure:
                    self.stats.on_swap_treasure()
                case _:
                    pass

            match type_cell_turn_end:
                case cell.CellClinic:
                    self.stats.restore_heal()
                case cell.CellArmory:
                    self.stats.restore_weapon()
                case cell.CellArmoryExplosive:
                    self.stats.restore_bombs()
                case cell.CellArmoryWeapon:
                    self.stats.restore_arrows()
                case _:
                    pass

        if response.get('hit'):
            dmg_pls: list[str] = response.get('dmg_pls')
            dead_pls: list[str] = response.get('dead_pls')
            drop_pls: list[str] = response.get('drop_pls')
            if self.name in dmg_pls:
                self.stats.on_take_dmg()


    def get_leaf_nodes(self):
        """
        :return: list of all leaves of a tree
        """
        leaves: list[FieldState] = []
        self._collect_leaf_nodes(self.root, leaves)
        return leaves

    def get_real_spawn_leaves(self):
        """
        :return: list of only real-spawn leaves of a tree
        """
        leaves: list[FieldState] = []
        self._collect_real_spawn_nodes(self.root, leaves)
        return leaves

    def get_compatible_leaves(self, target_player: str):
        """
        :return: list of all leaves of a tree which compatible with target player
        """
        leaves: list[FieldState] = []
        self._collect_compatible_nodes(self.root, leaves, target_player)
        return leaves

    def get_average_field(self):
        leaves = self.get_real_spawn_leaves()
        fields = [leaf.get_current_data()[0] for leaf in leaves]
        avg_field = self._calc_avg_field(fields)
        return avg_field

    def _collect_leaf_nodes(self, node: FieldState, leaves: list):
        if not node.next_states:
            leaves.append(node)
        for state in node.next_states:
            self._collect_leaf_nodes(state, leaves)

    def _collect_real_spawn_nodes(self, node: FieldState, leaves: list):
        if not node.next_states:
            leaves.append(node)
        for state in node.next_states:
            if state.is_real_spawn:
                self._collect_real_spawn_nodes(state, leaves)

    def _collect_compatible_nodes(self, node: FieldState, leaves: list, target_player: str):
        if not node.next_states:
            leaves.append(node)
        for state in node.next_states:
            if state.enemy_compatibility[target_player]:
                self._collect_compatible_nodes(state, leaves, target_player)

    def _calc_avg_field(self, fields: list[list[list]]):
        avg_field = {}
        for field in fields:
            for y, row in enumerate(field):
                if y not in avg_field:
                    avg_field |= {y: {}}
                for x, cell_obj in enumerate(row):
                    if x not in avg_field.get(y):
                        avg_field[y] |= {x: {}}
                    t_cell = type(cell)

                    if t_cell not in avg_field.get(y).get(x):
                        avg_field[y][x] |= {t_cell: {'amount': 0}}
                    if t_cell is CellRiver and cell_obj.direction not in avg_field.get(y).get(x).get(t_cell):
                        avg_field[y][x][t_cell] |= {cell_obj.direction: {'amount': 0}}

                    avg_field[y][x][t_cell]['amount'] += 1
                    if t_cell is CellRiver:
                        avg_field[y][x][t_cell][cell_obj.direction]['amount'] += 1

        return self.make_avg_field(avg_field)

    @staticmethod
    def make_avg_field(avg_field: dict) -> list[list[cell.CELL]]:
        field = []
        for row_idx in avg_field:
            field.append([])
            for col_idx in avg_field[row_idx]:
                cell_obj = avg_field[row_idx][col_idx]
                cell_type, direction = get_max_amount_cell(cell_obj)
                field[row_idx].append(cell_type(Position(col_idx, row_idx)))
        return field


def get_max_amount_cell(cell_data: dict):
    max_amount = 0
    max_type = NoneCell
    direction = None
    for c_type, data in cell_data.items():
        if data['amount'] > max_amount:
            max_amount = data['amount']
            max_type = c_type
    # if max_type is CellRiver:
    #     for r_dir, data in cell_data[max_type]
    return max_type, direction
