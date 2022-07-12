from copy import copy
from typing import Type

from GameEngine.entities.player import Player
from GameEngine.field import cell
from GameEngine.field import wall
from GameEngine.globalEnv.enums import Directions, Actions, TreasureTypes
from bots_ai.exceptions import UnreachableState
from bots_ai.field_obj import UnknownCell
from bots_ai.field_state import FieldState
from bots_ai.utils import _calc_possible_river_trajectories, get_possible_river_directions


class BotAI:
    def __init__(self, game_rules: dict, name: str, pos_x: int = None, pos_y: int = None):
        self.size_x = game_rules.get('generator_rules').get('cols')
        self.size_y = game_rules.get('generator_rules').get('rows')
        self.cols = 2 * self.size_x + 1 if pos_x is None else self.size_x + 2
        self.rows = 2 * self.size_y + 1 if pos_y is None else self.size_y + 2
        self.pos_x = pos_x + 1 if pos_x is not None else self.size_x
        self.pos_y = pos_y + 1 if pos_y is not None else self.size_y
        is_final_size = True if pos_x is not None and pos_y is not None else False
        field = self._generate_start_field()
        player = Player(field[self.pos_y][self.pos_x], name)
        self.unique_objects_types: list = self._get_unique_obj_types(game_rules)
        self.field_root = FieldState(field, player, None, copy(self.unique_objects_types),
                                     player.cell.x, player.cell.x, player.cell.y, player.cell.y,
                                     self.size_x, self.size_y, self.pos_x, self.pos_y, is_final_size)

    def get_fields(self) -> list[tuple[list[list[cell.Cell | None]], Player]]:
        """returns all leaves data of a tree"""
        leaves: list[FieldState] = []
        self._collect_leaf_nodes(self.field_root, leaves)
        return [leaf.get_current_data() for leaf in leaves]

    def process_turn_resp(self, raw_response: dict):
        action = Actions[raw_response.get('action')]
        direction = Directions[raw_response.get('direction')] if raw_response.get('direction') else None
        player_name: str = raw_response.get('player_name')
        response: dict = raw_response.get('response')

        action_to_processor = {
            Actions.swap_treasure: self._treasure_swap_processor,
            Actions.shoot_bow: self._shooting_processor,
            Actions.throw_bomb: self._bomb_throw_processor,
            Actions.skip: self._pass_processor,
            Actions.move: self._movement_processor,
            Actions.info: self._info_processor,
        }
        to_be_removed = []
        for node in self._get_leaf_nodes():
            res = action_to_processor[action](node, player_name, direction, response)
            if res:
                to_be_removed.append(res)
        for node in to_be_removed:
            node.remove()

    def _treasure_swap_processor(self, node: FieldState, player_name: str, direction: Directions | None,
                                 response: dict):
        pass

    def _shooting_processor(self, node: FieldState, player_name: str, direction: Directions, response: dict):
        pass

    def _bomb_throw_processor(self, node: FieldState, player_name: str, direction: Directions, response: dict):
        pass

    def _pass_processor(self, node: FieldState, player_name: str, direction: Directions | None, response: dict):
        pass

    def _movement_processor(self, node: FieldState, player_name: str, direction: Directions, response: dict):
        is_diff_cells: bool = response.get('diff_cells')
        type_cell_turn_end: Type[cell.Cell] = response.get('type_cell_at_end_of_turn')
        type_cell_after_wall_check: Type[cell.Cell] = response.get('type_cell_after_wall_check')
        is_wall_passed: bool = response.get('wall_passed')
        wall_type: Type[wall.WallEmpty] | None = response.get('wall_type')
        # todo учесть что это не обязательно настоящий тип стены
        cell_treasures_amount: int = response.get('cell_treasures_amount')
        type_out_treasure: TreasureTypes | None = response.get('type_out_treasure')

        start_cell = node.field[node.player.cell.y][node.player.cell.x]
        new_cell = start_cell.neighbours[direction]
        if not is_wall_passed:
            start_cell.add_wall(direction, wall_type())
            if new_cell:
                new_cell.add_wall(-direction, wall_type())
                if type(new_cell) is cell.CellRiver and new_cell.direction is -direction:
                    return node
                if type(start_cell) is cell.CellRiver and start_cell.direction is direction:
                    return node

            new_cell = start_cell
            direction = -direction
        elif type_cell_turn_end is not cell.CellExit:
            start_cell.add_wall(direction, wall.WallEmpty())
            if new_cell:
                new_cell.add_wall(-direction, wall.WallEmpty())

        # хотим пройти в выход, но он еще не создан
        if type_cell_turn_end is cell.CellExit and type(new_cell) is not cell.CellExit:
            exit_cell = node.create_exit(direction, start_cell)
            if not exit_cell:
                return node
            node.move_player(exit_cell)
            return

        #  попытка сходить за пределы карты - значит всю ветку можно удалить
        if new_cell is None:
            return node

        #  попытка изменить значение уже известной клетки
        if type(new_cell) not in [UnknownCell, type_cell_after_wall_check]:
            return node

        #  перемещение в указанную сторону не противоречит известному полю
        if type_cell_after_wall_check is not cell.CellRiver:
            if type(new_cell) is UnknownCell:
                if type_cell_after_wall_check in self.unique_objects_types \
                        and type_cell_after_wall_check not in node.remaining_unique_obj_types:
                    return node
                node.update_cell_type(type_cell_after_wall_check, new_cell.x, new_cell.y)
            node.move_player(new_cell)
            return

        # ... , река-река / река-устье / река, ...
        # река-река: type_cell_after_wall_check == river, type_cell_turn_end == river, is_diff_cells = True
        # река-устье: type_cell_after_wall_check == river, type_cell_turn_end == mouth, is_diff_cells = True
        # река: type_cell_after_wall_check == river, type_cell_turn_end == river, is_diff_cells = False
        try:
            _calc_possible_river_trajectories(
                node, new_cell, type_cell_after_wall_check, type_cell_turn_end, is_diff_cells, direction)
        except UnreachableState:
            return node

    def _info_processor(self, node: FieldState, player_name: str, direction: Directions, response: dict):
        type_cell_turn_end: Type[cell.Cell] = response.get('type_cell_at_end_of_turn')
        cell_treasures_amount: int = response.get('cell_treasures_amount')

        pos_x = node.player.cell.x
        pos_y = node.player.cell.y
        if type_cell_turn_end is not cell.CellRiver:
            if type_cell_turn_end in self.unique_objects_types and type_cell_turn_end not in node.remaining_unique_obj_types:
                return node
            node.update_cell_type(type_cell_turn_end, pos_x, pos_y)
            node.move_player(node.field[pos_y][pos_x])
        else:
            possible_directions = get_possible_river_directions(node.player.cell)
            [node.add_modified_leaf(node.player.cell, type_cell_turn_end, dir_) for dir_ in possible_directions]

    @staticmethod
    def _get_unique_obj_types(rules: dict):
        unique_obj = [cell.CellExit, cell.CellArmory, cell.CellClinic]
        return unique_obj

    def _collect_leaf_nodes(self, node: FieldState, leaves: list[FieldState]):
        if node is not None:
            if not node.next_states:
                leaves.append(node)
            for n in node.next_states:
                self._collect_leaf_nodes(n, leaves)

    def _get_leaf_nodes(self) -> list[FieldState]:
        leaves: list[FieldState] = []
        self._collect_leaf_nodes(self.field_root, leaves)
        return leaves

    def _generate_start_field(self):
        field = [[UnknownCell(col, row)
                  if row not in [0, self.rows - 1] and col not in [0, self.cols - 1] else None
                  for col in range(self.cols)] for row in range(self.rows)]
        self._generate_connections(field)
        return field

    def _generate_connections(self, field):
        for row in range(self.rows):
            for col in range(self.cols):
                if field[row][col] is not None:
                    neighbours = {}
                    for direction in Directions:
                        x, y = direction.calc(col, row)
                        if x in range(self.cols) and y in range(self.rows) and isinstance(field[y][x], cell.Cell):
                            neighbours.update({direction: field[y][x]})
                        else:
                            neighbours.update({direction: None})

                    field[row][col].change_neighbours(neighbours)


if __name__ == "__main__":
    # bot = BotAI(base_rules, '')
    # for row_ in bot.field_root.field:
    #     print(row_)
    pass
