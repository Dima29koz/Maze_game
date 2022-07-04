from copy import copy, deepcopy
from typing import Type

from GameEngine.entities.player import Player
from GameEngine.field import cell
from GameEngine.field import wall
from GameEngine.globalEnv.enums import Directions, Actions, TreasureTypes
from GameEngine.field import response as r
from GameEngine.rules import rules as base_rules


class UnknownWall(wall.WallEmpty):
    def __init__(self):
        super().__init__()


class UnknownCell(cell.Cell):
    def __init__(self, x: int, y: int):
        super().__init__(x, y)
        self.x, self.y = x, y
        self.neighbours: dict[Directions, cell.Cell | None] = {
            Directions.top: None,
            Directions.right: None,
            Directions.bottom: None,
            Directions.left: None}
        self.walls: dict[Directions, UnknownWall] = {
            Directions.top: UnknownWall(),
            Directions.right: UnknownWall(),
            Directions.bottom: UnknownWall(),
            Directions.left: UnknownWall()}

    def __repr__(self):
        return '?'


class FieldState:
    """
    contains current field state known by player
    """
    def __init__(self, field: list[list[cell.Cell | None]], player: Player):
        self.field = field
        self.player = player
        self.next_states: list[FieldState] = []

    def get_current_data(self):
        return self.field, self.player

    def update_cell_type(self, new_type: Type[cell.Cell], pos_x: int, pos_y: int):
        neighbours = self.field[pos_y][pos_x].neighbours
        walls = self.field[pos_y][pos_x].walls
        self.field[pos_y][pos_x] = new_type(pos_x, pos_y)
        self.field[pos_y][pos_x].change_neighbours(neighbours)
        self.field[pos_y][pos_x].walls = walls

    def create_exit(self, direction: Directions, current_cell: cell.Cell):
        cell_exit = cell.CellExit(
            *direction.calc(current_cell.x, current_cell.y), -direction, cell=current_cell)
        current_cell.add_wall(direction, wall.WallExit())
        current_cell.neighbours[direction] = cell_exit
        self.field[cell_exit.y][cell_exit.x] = cell_exit
        return cell_exit


class BotAI:
    def __init__(self, game_rules: dict, name: str, pos_x: int = None, pos_y: int = None):
        self.size_x = game_rules.get('generator_rules').get('cols')
        self.size_y = game_rules.get('generator_rules').get('rows')
        self.cols = 2 * self.size_x + 1
        self.rows = 2 * self.size_y + 1
        self.pos_x = pos_x if pos_x else self.size_x
        self.pos_y = pos_y if pos_y else self.size_y
        field = self._generate_start_field()
        player = Player(field[self.pos_y][self.pos_x], name)
        self.field_root = FieldState(field, player)

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
        for node in self._get_leaf_nodes():
            action_to_processor[action](node, player_name, direction, response)

    def _treasure_swap_processor(self, node: FieldState, player_name: str, direction: Directions | None, response: dict):
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

        current_cell = node.player.cell
        if not is_wall_passed:
            current_cell.add_wall(direction, wall_type())
            if current_cell.neighbours[direction]:
                current_cell.neighbours[direction].add_wall(-direction, wall_type())
        else:  # coords changed
            if type_cell_turn_end is cell.CellExit:
                current_cell = node.create_exit(direction, current_cell)
            else:
                current_cell = current_cell.neighbours[direction]
                pos_x = current_cell.x
                pos_y = current_cell.y
                node.update_cell_type(type_cell_after_wall_check, pos_x, pos_y)
            node.player.move(current_cell)
        if type_cell_after_wall_check is not cell.CellRiver or not is_diff_cells:
            # coords changed ones, only 1 possible new location
            return
        # print('smilo')
        node.next_states = self._calc_possible_river_trajectories(
            node, current_cell, type_cell_after_wall_check, type_cell_turn_end)

    def _info_processor(self, node: FieldState, player_name: str, direction: Directions, response: dict):
        type_cell_turn_end = response.get('type_cell_at_end_of_turn')
        cell_treasures_amount: int = response.get('cell_treasures_amount')

        pos_x = node.player.cell.x
        pos_y = node.player.cell.y
        node.update_cell_type(type_cell_turn_end, pos_x, pos_y)

    def _calc_possible_river_trajectories(
            self, node: FieldState, current_cell: cell.Cell,
            type_cell_after_wall_check: Type[cell.Cell],
            type_cell_turn_end: Type[cell.Cell]):
        new_states = []
        possible_len = [1, 2] if type_cell_turn_end is cell.CellRiverMouth else [2]
        for length in possible_len:
            req_cell_type = type_cell_turn_end if length == 1 else cell.CellRiver
            for direction in Directions:
                if type(current_cell.neighbours[direction]) in [req_cell_type, UnknownCell]:
                    new_location = current_cell.neighbours[direction]
                    if length > 1:
                        for dir_ in Directions:
                            if type(new_location.neighbours[dir_]) in [type_cell_turn_end, UnknownCell]:
                                final_location = new_location.neighbours[dir_]
                                new_node = deepcopy(node)
                                new_node.update_cell_type(req_cell_type, new_location.x, new_location.y)
                                new_node.update_cell_type(type_cell_turn_end, final_location.x, final_location.y)
                                new_node.player.move(final_location)
                                new_states.append(new_node)
                    else:
                        new_node = deepcopy(node)
                        new_node.update_cell_type(req_cell_type, new_location.x, new_location.y)
                        new_node.player.move(new_location)
                        new_states.append(new_node)

        return new_states

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
                  if row not in [0, self.rows-1] and col not in [0, self.cols-1] else None
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
    bot = BotAI(base_rules, '')
    for row_ in bot.field_root.field:
        print(row_)
