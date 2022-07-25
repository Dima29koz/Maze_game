from copy import copy
from typing import Type, Union

from GameEngine.field import cell, wall
from GameEngine.globalEnv.enums import Directions, Actions, TreasureTypes
from bots_ai.exceptions import UnreachableState
from bots_ai.field_obj import UnknownCell, UnknownWall, UnbreakableWall

CELL = Union[
    cell.Cell, cell.CellRiver, cell.CellRiverMouth,
    cell.CellExit, cell.CellClinic, cell.CellArmory,
    cell.CellArmoryExplosive, cell.CellArmoryWeapon, UnknownCell]


class FieldState:
    """
    contains current field state known by player
    """

    def __init__(self, field: list[list[CELL | None]],
                 remaining_obj_amount: dict,
                 size_x: int, size_y: int,
                 pl_pos_x: int = None, pl_pos_y: int = None,
                 parent=None):
        self.field = field
        self.size_x = size_x
        self.size_y = size_y
        self.pl_pos_x = pl_pos_x if pl_pos_x is not None else 0
        self.pl_pos_y = pl_pos_y if pl_pos_y is not None else 0
        self.remaining_obj_amount = remaining_obj_amount
        self.next_states: list[FieldState] = []
        self.parent: FieldState | None = parent
        self.is_real = False

    def get_current_data(self):
        return self.field, {'x': self.pl_pos_x, 'y': self.pl_pos_y}

    def get_player_cell(self):
        return self.field[self.pl_pos_y][self.pl_pos_x]

    def remove(self):
        self.parent._remove_leaf(self)

    def process_action(self, action: Actions, direction: Directions | None, response: dict):
        action_to_processor = {
            Actions.swap_treasure: self._treasure_swap_processor,
            Actions.shoot_bow: self._shooting_processor,
            Actions.throw_bomb: self._bomb_throw_processor,
            Actions.skip: self._pass_processor,
            Actions.move: self._movement_processor,
            Actions.info: self._info_processor,
        }

        try:
            action_to_processor[action](direction, response)
        except UnreachableState:
            self.remove()

    def copy(self, pl_pos_x: int = None, pl_pos_y: int = None):
        if pl_pos_x is None and pl_pos_y is None:
            pl_pos_x, pl_pos_y = self.pl_pos_x, self.pl_pos_y
        return FieldState(
            [copy(row) for row in self.field],
            copy(self.remaining_obj_amount),
            self.size_x, self.size_y,
            pl_pos_x, pl_pos_y,
            self)

    def get_leaf_nodes(self):
        leaves: list[FieldState] = []
        self._collect_leaf_nodes(leaves)
        return leaves

    def _collect_leaf_nodes(self, leaves: list):
        if not self.next_states:
            leaves.append(self)
        for state in self.next_states:
            state._collect_leaf_nodes(leaves)

    def _move_player(self, target_cell: CELL):
        self.pl_pos_x, self.pl_pos_y = target_cell.x, target_cell.y

    def _update_cell_type(self, new_type: Type[CELL] | None, pos_x: int, pos_y: int,
                          direction: Directions = None):

        target_cell = self.field[pos_y][pos_x] if new_type is not cell.CellExit else self._get_neighbour_cell(
            self.field[pos_y][pos_x], direction)
        if target_cell is not None and new_type not in [cell.CellRiverMouth, cell.CellRiver]:
            if self._has_known_input_river(target_cell, direction, ignore_dir=True):
                raise UnreachableState()
        if target_cell is not None and new_type is not cell.CellRiver:
            if self._is_cause_of_isolated_mouth(target_cell):
                raise UnreachableState()

        if new_type is None:
            if self.field[pos_y][pos_x] is None or type(self.field[pos_y][pos_x]) is cell.CellExit:
                return
            self.field[pos_y][pos_x] = None
            return

        if new_type is cell.CellExit:
            if type(target_cell) is not UnknownCell and target_cell is not None:
                raise UnreachableState()
            self._create_exit(direction, self.field[pos_y][pos_x])
            return

        # todo кажется надо убедиться что я не клоун, ибо а зачем обновлять тип известной клетки
        if type(self.field[pos_y][pos_x]) is UnknownCell:
            try:
                if self.remaining_obj_amount.get(new_type) == 0:
                    raise UnreachableState()
                self.remaining_obj_amount[new_type] -= 1
            except KeyError:
                pass

        walls = self.field[pos_y][pos_x].walls
        self.field[pos_y][pos_x] = new_type(pos_x, pos_y) if not direction else cell.CellRiver(pos_x, pos_y, direction)
        self.field[pos_y][pos_x].walls = copy(walls)

        if direction:
            self._add_wall(self.field[pos_y][pos_x], direction, wall.WallEmpty)

    def _create_exit(self, direction: Directions, current_cell: cell.Cell) -> None:
        """

        :param direction: direction of exit wall
        :param current_cell: position of cell which neighbour`s to exit
        """
        cell_exit = cell.CellExit(*direction.calc(current_cell.x, current_cell.y), -direction)
        for dir_ in Directions:
            if dir_ is -direction:
                continue
            neighbour_cell = self._get_neighbour_cell(cell_exit, dir_)
            if neighbour_cell:
                if type(neighbour_cell) is cell.CellExit:
                    continue
                self._update_wall(neighbour_cell, -dir_, wall.WallOuter)
        current_cell.add_wall(direction, wall.WallExit())
        self.field[cell_exit.y][cell_exit.x] = cell_exit

    def _add_wall(self, current_cell: CELL, direction: Directions, wall_type: Type[wall.WallEmpty],
                  neighbour_wall_type: Type[wall.WallEmpty] | None = None):
        self._update_wall(current_cell, direction, wall_type)
        neighbour = self._get_neighbour_cell(current_cell, direction)
        if neighbour:
            if neighbour_wall_type is None:
                neighbour_wall_type = wall_type
            self._update_wall(neighbour, -direction, neighbour_wall_type)

    def _update_wall(self, target_cell: CELL, direction: Directions, wall_type):
        if type(self.field[target_cell.y][target_cell.x].walls[direction]) is wall_type:
            return
        self.field[target_cell.y][target_cell.x] = copy(self.field[target_cell.y][target_cell.x])
        self.field[target_cell.y][target_cell.x].walls = copy(self.field[target_cell.y][target_cell.x].walls)
        self.field[target_cell.y][target_cell.x].add_wall(direction, wall_type())

    def _get_neighbour_cell(self, current_cell: CELL, direction: Directions):
        x, y = direction.calc(current_cell.x, current_cell.y)
        try:
            return self.field[y][x]
        except IndexError:
            return None

    def _remove_leaf(self, leaf):
        self.next_states.remove(leaf)
        if not self.next_states and self.parent:
            self.parent._remove_leaf(self)

    def _set_parent(self, node):
        self.parent = node

    def _add_modified_leaf(self, target_cell: CELL, new_type: Type[CELL], direction: Directions = None):
        self.next_states.append(self._get_modified_copy(target_cell, new_type, direction))

    def _get_modified_copy(self, target_cell: CELL, new_type: Type[CELL], direction: Directions = None):
        new_state = self.copy()
        new_state._update_cell_type(new_type, target_cell.x, target_cell.y, direction)
        if new_state.pl_pos_x != target_cell.x or new_state.pl_pos_y != target_cell.y:
            new_state._move_player(target_cell)
        return new_state

    def _treasure_swap_processor(self, direction: Directions | None, response: dict):
        pass

    def _shooting_processor(self, direction: Directions, response: dict):
        is_hit: bool = response.get('hit')
        dmg_pls: list[str] = response.get('dmg_pls')
        dead_pls: list[str] = response.get('dead_pls')
        drop_pls: list[str] = response.get('drop_pls')

        #  todo add logic here

        self._pass_processor(direction, response)

    def _bomb_throw_processor(self, direction: Directions, response: dict) -> None:
        is_destroyed: bool = response.get('destroyed')

        current_cell = self.get_player_cell()
        if is_destroyed:
            if not current_cell.walls[direction].breakable:
                raise UnreachableState()
            self._add_wall(current_cell, direction, wall.WallEmpty)
        else:
            if current_cell.walls[direction].breakable and type(current_cell.walls[direction]) is not UnknownWall:
                raise UnreachableState()
            if type(current_cell.walls[direction]) is UnknownWall:
                self._add_wall(current_cell, direction, UnbreakableWall)

        self._pass_processor(direction, response)

    def _pass_processor(self, direction: Directions | None, response: dict):
        type_cell_turn_end: Type[cell.Cell] = response.get('type_cell_at_end_of_turn')
        cell_treasures_amount: int = response.get('cell_treasures_amount')
        type_out_treasure: TreasureTypes | None = response.get('type_out_treasure')

        current_cell = self.get_player_cell()
        if type(current_cell) is not cell.CellRiver:
            return  # todo add cell mechanics activator
        end_cell = self._get_neighbour_cell(current_cell, current_cell.direction)
        if type(end_cell) not in [type_cell_turn_end, UnknownCell]:
            raise UnreachableState()
        if type(end_cell) is type_cell_turn_end:
            neighbour_cell = self._get_neighbour_cell(current_cell, current_cell.direction)
            self._move_player(neighbour_cell)
        elif type_cell_turn_end is cell.CellRiver:
            self._calc_possible_river_trajectories(
                end_cell, type_cell_turn_end, type_cell_turn_end, False, current_cell.direction)
        elif type_cell_turn_end is cell.CellRiverMouth:
            self._update_cell_type(type_cell_turn_end, end_cell.x, end_cell.y)
            self._move_player(end_cell)
        else:
            raise UnreachableState()

    def _movement_processor(self, direction: Directions, response: dict):
        is_diff_cells: bool = response.get('diff_cells')
        type_cell_turn_end: Type[CELL] = response.get('type_cell_at_end_of_turn')
        type_cell_after_wall_check: Type[CELL] = response.get('type_cell_after_wall_check')
        is_wall_passed: bool = response.get('wall_passed')
        wall_type: Type[wall.WallEmpty] | None = response.get('wall_type')
        # todo учесть что это не обязательно настоящий тип стены
        cell_treasures_amount: int = response.get('cell_treasures_amount')
        type_out_treasure: TreasureTypes | None = response.get('type_out_treasure')

        start_cell = self.get_player_cell()
        new_cell = self._get_neighbour_cell(start_cell, direction)
        if not is_wall_passed:
            if new_cell:
                if type(new_cell) is cell.CellRiver and new_cell.direction is -direction:
                    raise UnreachableState()
                if type(start_cell) is cell.CellRiver and start_cell.direction is direction:
                    raise UnreachableState()
            self._add_wall(start_cell, direction, wall_type)

            new_cell = start_cell
            direction = -direction
        elif type_cell_turn_end is not cell.CellExit and type(start_cell) is not cell.CellExit:
            self._add_wall(start_cell, direction, wall.WallEmpty)

        # хотим пройти в выход, но он еще не создан
        if type_cell_turn_end is cell.CellExit and type(new_cell) is not cell.CellExit:
            self._update_cell_type(cell.CellExit, start_cell.x, start_cell.y, direction)
            new_cell = self._get_neighbour_cell(start_cell, direction)

        #  попытка сходить за пределы карты - значит всю ветку можно удалить
        if new_cell is None:
            raise UnreachableState()

        #  попытка изменить значение уже известной клетки
        if type(new_cell) not in [UnknownCell, type_cell_after_wall_check]:
            raise UnreachableState()

        #  перемещение в указанную сторону не противоречит известному полю
        if type_cell_after_wall_check is not cell.CellRiver:
            if type(new_cell) is UnknownCell:
                self._update_cell_type(type_cell_after_wall_check, new_cell.x, new_cell.y)
            self._move_player(new_cell)
            return

        # ... , река-река / река-устье / река, ...
        # река-река: type_cell_after_wall_check == river, type_cell_turn_end == river, is_diff_cells = True
        # река-устье: type_cell_after_wall_check == river, type_cell_turn_end == mouth, is_diff_cells = True
        # река: type_cell_after_wall_check == river, type_cell_turn_end == river, is_diff_cells = False

        self._calc_possible_river_trajectories(
            new_cell, type_cell_after_wall_check, type_cell_turn_end, is_diff_cells, direction)

    def _info_processor(self, direction: Directions, response: dict):
        type_cell_turn_end: Type[cell.Cell] = response.get('type_cell_at_end_of_turn')
        cell_treasures_amount: int = response.get('cell_treasures_amount')

        if type_cell_turn_end is not cell.CellRiver:
            self._update_cell_type(type_cell_turn_end, self.pl_pos_x, self.pl_pos_y)
        else:
            player_cell = self.get_player_cell()
            possible_directions = self._get_possible_river_directions(player_cell)
            [self._add_modified_leaf(player_cell, type_cell_turn_end, dir_) for dir_ in possible_directions]

    def _calc_possible_river_trajectories(
            self, current_cell: CELL,
            type_cell_after_wall_check: Type[CELL],
            type_cell_turn_end: Type[CELL], is_diff_cells: bool, turn_direction: Directions):
        # ... , река, ...
        if type_cell_after_wall_check is cell.CellRiver and not is_diff_cells:
            next_states = self._get_possible_leaves(current_cell, turn_direction)
            if not (len(next_states) == 1 and next_states[0] is self):
                [state._set_parent(self) for state in next_states]
                self.next_states = next_states
            return

        # ... , река-река / река-устье, ...

        # все варианты течения первой клетки
        new_states = self._get_possible_leaves(current_cell, turn_direction, washed=True)

        if type_cell_turn_end is not cell.CellRiverMouth:
            # все варианты течения второй клетки
            new_states2: list[FieldState] = []
            for new_state in new_states:
                riv_dir = new_state.get_player_cell().direction
                try:
                    new_states2 += new_state._get_possible_leaves(
                        new_state._get_neighbour_cell(new_state.get_player_cell(), riv_dir), riv_dir)
                except UnreachableState:
                    pass
            final_states: list[FieldState] = []
            for new_state in new_states2:
                riv_dir = new_state.get_player_cell().direction
                try:
                    final_states += new_state._get_possible_leaves(
                        new_state._get_neighbour_cell(new_state.get_player_cell(), riv_dir), riv_dir)
                except UnreachableState:
                    pass
            if not final_states:
                raise UnreachableState()
            if not (len(final_states) == 1 and final_states[0] is self):
                [state._set_parent(self) for state in final_states]
                self.next_states = final_states
            return
        else:  # смыло до устья
            final_states: list[FieldState] = []
            new_states2: list[FieldState] = []
            for new_state in new_states:
                riv_dir = new_state.get_player_cell().direction
                current_cell = new_state._get_neighbour_cell(new_state.get_player_cell(), riv_dir)
                if type(current_cell) is cell.CellRiverMouth:
                    new_state._move_player(current_cell)
                    final_states.append(new_state)
                else:
                    try:
                        new_states2 += new_state._get_possible_leaves(current_cell, riv_dir)
                    except UnreachableState:
                        pass
                    if type(current_cell) is UnknownCell:
                        try:
                            final_states.append(new_state._get_modified_copy(current_cell, type_cell_turn_end))
                        except UnreachableState:
                            pass

            for new_state in new_states2:
                riv_dir = new_state.get_player_cell().direction
                current_cell = new_state._get_neighbour_cell(new_state.get_player_cell(), riv_dir)
                if type(current_cell) is cell.CellRiverMouth:
                    new_state._move_player(current_cell)
                    final_states.append(new_state)
                else:
                    try:
                        final_states.append(new_state._get_modified_copy(current_cell, type_cell_turn_end))
                    except UnreachableState:
                        pass
            if not final_states:
                raise UnreachableState()
            if not (len(final_states) == 1 and final_states[0] is self):
                [state._set_parent(self) for state in final_states]
                self.next_states = final_states
            return

    def _get_possible_leaves(
            self, current_cell: CELL, turn_direction: Directions = None, is_final: bool = False,
            washed: bool = False, next_cell_is_mouth: bool = False):

        if washed:
            prev_cell = self._get_neighbour_cell(current_cell, -turn_direction)
            if type(prev_cell) is cell.CellRiver and prev_cell.direction is turn_direction:
                return []

        possible_river_dirs = self._get_possible_river_directions(current_cell, turn_direction, washed,
                                                                  next_cell_is_mouth)
        if not possible_river_dirs:
            return []

        if type(current_cell) is UnknownCell:
            leaves = [self._get_modified_copy(current_cell, cell.CellRiver, direction)
                      for direction in possible_river_dirs]
            return leaves
        elif type(current_cell) is cell.CellRiver and current_cell.direction in possible_river_dirs:
            self._move_player(current_cell)
            return [self]
        else:
            return []

    def _get_possible_river_directions(self, river_cell: CELL, turn_direction: Directions = None,
                                       washed: bool = False, next_cell_is_mouth: bool = False) -> list[Directions]:
        dirs = []

        if not washed and turn_direction:
            prev_cell = self._get_neighbour_cell(river_cell, -turn_direction)
            if type(prev_cell) is cell.CellRiverMouth or (
                    type(prev_cell) is cell.CellRiver and prev_cell.direction is not turn_direction):
                if not self._has_known_input_river(prev_cell, -turn_direction):
                    if self._is_river_is_looped(river_cell, prev_cell):
                        return []
                    return [-turn_direction]
                else:
                    return []

        for direction in Directions:
            # река не может течь в стену
            if type(river_cell.walls[direction]) not in [wall.WallEmpty, UnknownWall]:
                continue
            neighbour_cell = self._get_neighbour_cell(river_cell, direction)
            if neighbour_cell is None:
                continue

            # река не может течь в сушу
            if type(neighbour_cell) not in [cell.CellRiver, cell.CellRiverMouth, UnknownCell]:
                continue

            # реки не могут течь друг в друга
            if type(neighbour_cell) is cell.CellRiver and neighbour_cell.direction is -direction:
                continue

            # река не имеет развилок
            if self._has_known_input_river(neighbour_cell, direction):
                continue

            if type(neighbour_cell) is cell.CellRiverMouth and self._is_the_only_allowed_dir(neighbour_cell, direction):
                return [direction]

            # нет стены между соседом, сосед  - река / устье / неизвестная_клетка, в соседа ничего не втекает

            # если смыло, то река не может течь в клетку откуда пришли
            if washed and direction is -turn_direction:
                continue

            if self._is_river_is_looped(river_cell, neighbour_cell):
                continue

            dirs.append(direction)
        return dirs

    def _has_known_input_river(self, target_cell: CELL, turn_direction: Directions, ignore_dir=False) -> bool:
        """

        :param target_cell: cell to be checked
        :param turn_direction: direction of turn
        :param ignore_dir: if True all directions will be checked
        :return: True if target_cell has known input river
        """
        for direction in Directions:
            if not ignore_dir and direction is -turn_direction:
                continue
            neighbour_cell = self._get_neighbour_cell(target_cell, direction)
            if type(neighbour_cell) is cell.CellRiver and neighbour_cell.direction is -direction:
                return True

    def _is_the_only_allowed_dir(self, target_cell: CELL, turn_direction: Directions) -> bool:
        """

        :param target_cell: cell to be checked
        :param turn_direction: direction of turn
        :return: True if target cell have only 1 possible direction to input
        """
        for direction in Directions:
            if direction is -turn_direction:
                continue
            neighbour_cell = self._get_neighbour_cell(target_cell, direction)
            if (type(neighbour_cell) is cell.CellRiver and neighbour_cell.direction is -direction) or \
                    type(neighbour_cell) is UnknownCell:
                return False
        return True

    def _is_river_is_looped(self, start_cell: cell.CellRiver, previous_cell: CELL) -> bool:
        """

        :param start_cell: current river cell
        :param previous_cell: previous river cell
        :return: True if river is circled
        """
        if start_cell.x == previous_cell.x and start_cell.y == previous_cell.y:
            return True
        if type(previous_cell) is cell.CellRiver:
            return self._is_river_is_looped(start_cell, self._get_neighbour_cell(previous_cell, previous_cell.direction))
        return False

    def _is_cause_of_isolated_mouth(self, target_cell) -> bool:
        for direction in Directions:
            neighbour_cell = self._get_neighbour_cell(target_cell, direction)
            if neighbour_cell and type(neighbour_cell) is cell.CellRiverMouth:
                if self._is_the_only_allowed_dir(neighbour_cell, direction):
                    return True
        return False
