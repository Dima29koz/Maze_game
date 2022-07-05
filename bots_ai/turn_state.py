from copy import deepcopy
from typing import Type

from GameEngine.entities.player import Player
from GameEngine.field import cell
from GameEngine.field import wall
from GameEngine.globalEnv.enums import Directions, Actions, TreasureTypes
from GameEngine.rules import rules as base_rules
from bots_ai.exceptions import UnreachableState


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

    def __init__(self, field: list[list[cell.Cell | None]], player: Player, parent):
        self.field = field
        self.player = player
        self.next_states: list[FieldState] = []
        self.parent: FieldState | None = parent

    def get_current_data(self):
        return self.field, self.player

    def update_cell_type(self, new_type: Type[cell.Cell], pos_x: int, pos_y: int, river_direction: Directions = None):
        neighbours = self.field[pos_y][pos_x].neighbours
        walls = self.field[pos_y][pos_x].walls
        self.field[pos_y][pos_x] = new_type(pos_x, pos_y) if not river_direction else new_type(pos_x, pos_y,
                                                                                               river_direction)
        self.field[pos_y][pos_x].change_neighbours(neighbours)
        self.field[pos_y][pos_x].walls = walls
        for direction in Directions:
            if self.field[pos_y][pos_x].neighbours[direction]:
                self.field[pos_y][pos_x].neighbours[direction].neighbours[-direction] = self.field[pos_y][pos_x]

    def create_exit(self, direction: Directions, current_cell: cell.Cell):
        target_cell = current_cell.neighbours[direction]
        if type(target_cell) is not UnknownCell and target_cell is not None:
            return
        cell_exit = cell.CellExit(
            *direction.calc(current_cell.x, current_cell.y), -direction, cell=current_cell)
        current_cell.add_wall(direction, wall.WallExit())
        current_cell.neighbours[direction] = cell_exit
        self.field[cell_exit.y][cell_exit.x] = cell_exit
        return cell_exit

    def remove_leaf(self, leaf):
        self.next_states.remove(leaf)
        if not self.next_states and self.parent:
            self.parent.remove_leaf(self)

    def remove(self):
        self.parent.remove_leaf(self)

    def set_parent(self, node):
        self.parent = node

    def add_modified_leaf(self, target_cell: cell.Cell, new_type: Type[cell.Cell], direction: Directions = None):
        self.next_states.append(self.get_modified_copy(target_cell, new_type, direction))

    def get_modified_copy(self, target_cell: cell.Cell, new_type: Type[cell.Cell], direction: Directions = None):
        new_state = FieldState(deepcopy(self.field), deepcopy(self.player), self)
        new_state.update_cell_type(new_type, target_cell.x, target_cell.y, direction)
        if new_state.player.cell != target_cell:
            new_state.player.move(target_cell)
        return new_state


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
        self.field_root = FieldState(field, player, None)

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
                start_cell.neighbours[direction].add_wall(-direction, wall_type())
            new_cell = start_cell

        # хотим пройти в выход, но он еще не создан
        if type_cell_turn_end is cell.CellExit and type(new_cell) is not cell.CellExit:
            exit_cell = node.create_exit(direction, start_cell)
            if not exit_cell:
                return node
            node.player.move(exit_cell)
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
                node.update_cell_type(type_cell_after_wall_check, new_cell.x, new_cell.y)
            node.player.move(new_cell)
            return

        # ... , река-река / река-устье / река, ...
        # река-река: type_cell_after_wall_check == river, type_cell_turn_end == river, is_diff_cells = True
        # река-устье: type_cell_after_wall_check == river, type_cell_turn_end == mouth, is_diff_cells = True
        # река: type_cell_after_wall_check == river, type_cell_turn_end == river, is_diff_cells = False
        try:
            new_states = self._calc_possible_river_trajectories(
                node, new_cell, type_cell_after_wall_check, type_cell_turn_end, is_diff_cells, direction)
        except UnreachableState:
            return node
        else:
            if new_states:
                node.next_states = new_states
                [leaf.set_parent(node) for leaf in node.next_states]

    def _info_processor(self, node: FieldState, player_name: str, direction: Directions, response: dict):
        type_cell_turn_end: Type[cell.Cell] = response.get('type_cell_at_end_of_turn')
        cell_treasures_amount: int = response.get('cell_treasures_amount')

        pos_x = node.player.cell.x
        pos_y = node.player.cell.y
        if type_cell_turn_end is not cell.CellRiver:
            node.update_cell_type(type_cell_turn_end, pos_x, pos_y)
        else:
            possible_directions = self._get_possible_river_directions(node.player.cell)
            [node.add_modified_leaf(node.player.cell, type_cell_turn_end, dir_) for dir_ in possible_directions]

    def _get_possible_river_directions(self, river_cell: cell.Cell) -> list[Directions]:
        dirs = []

        for direction in Directions:
            neighbour_cell = river_cell.neighbours[direction]
            if neighbour_cell is None:
                continue
            elif type(neighbour_cell) is UnknownCell:
                dirs.append(direction)
            elif type(neighbour_cell) is cell.CellRiver and neighbour_cell.direction is not -direction:
                dirs.append(direction)
            elif type(neighbour_cell) is cell.CellRiverMouth:
                semi_neighbour_cells = []
                has_in_river = False
                for dir_ in Directions:
                    if dir_ is -direction:
                        continue
                    semi_neighbour_cell = neighbour_cell.neighbours[dir_]
                    if type(semi_neighbour_cell) is cell.CellRiver and semi_neighbour_cell.direction is -dir_:
                        has_in_river = True
                    semi_neighbour_cells.append(semi_neighbour_cell)  # 3 соседа устья

                has_unknown_neighbour = UnknownCell not in [type(semi_neighbour_cell) for semi_neighbour_cell in
                                                            semi_neighbour_cells]
                if not has_in_river:
                    if has_unknown_neighbour:
                        dirs.append(direction)
                    else:
                        return [direction]
        return dirs

    def _calc_possible_river_trajectories(
            self, node: FieldState, current_cell: cell.Cell,
            type_cell_after_wall_check: Type[cell.Cell],
            type_cell_turn_end: Type[cell.Cell], is_diff_cells: bool, turn_direction: Directions):
        new_states = []

        # ... , река, ...
        if type_cell_after_wall_check is cell.CellRiver and not is_diff_cells:
            if type(current_cell) not in [UnknownCell, cell.CellRiver]:
                raise UnreachableState()
            possible_river_dirs = self._get_possible_river_dirs_on_walk(current_cell, turn_direction)
            print(possible_river_dirs)
            if type(current_cell) is UnknownCell:
                for direction in possible_river_dirs:
                    node.add_modified_leaf(current_cell, type_cell_after_wall_check, direction)
                return
            elif type(current_cell) is cell.CellRiver and current_cell.direction in possible_river_dirs:
                if node.player.cell != current_cell:
                    node.player.move(current_cell)
                return
            raise UnreachableState()

        # ... , река-река / река-устье, ...
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

    def _get_possible_river_dirs_on_walk(self, current_cell: cell.Cell, turn_direction: Directions):
        prev_cell = current_cell.neighbours[-turn_direction]
        if type(prev_cell) is cell.CellRiverMouth:
            return [-turn_direction]
        else:  # пришли с реки
            if prev_cell.direction is turn_direction:
                return [dir_ for dir_ in Directions if dir_ is not -turn_direction]
            else:
                return [-turn_direction]

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
    bot = BotAI(base_rules, '')
    for row_ in bot.field_root.field:
        print(row_)
