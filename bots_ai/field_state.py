from copy import deepcopy, copy
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

    def __init__(self, field: list[list[CELL | None]], pl_pos_x: int, pl_pos_y: int, parent,
                 remaining_unique_obj_types: list,
                 min_x, max_x, min_y, max_y, size_x, size_y, start_x, start_y,
                 is_final_size: bool = False):
        self.field = field
        self.pl_pos_x = pl_pos_x
        self.pl_pos_y = pl_pos_y
        self.size_x = size_x
        self.size_y = size_y
        self.start_x = start_x
        self.start_y = start_y
        self.min_x = min_x
        self.max_x = max_x
        self.min_y = min_y
        self.max_y = max_y
        self.is_final_size = is_final_size
        self.remaining_unique_obj_types = remaining_unique_obj_types
        self.next_states: list[FieldState] = []
        self.parent: FieldState | None = parent

    # def get_field_copy(self):
    #     return [
    #         [
    #             type(_cell)(_cell.x, _cell.y, _cell.direction) if type(_cell) is cell.CellRiver
    #             else type(_cell)(_cell.x, _cell.y) if _cell is not None else None for _cell in row
    #         ] for row in self.field]

    def get_current_data(self):
        return self.field, {'x': self.pl_pos_x, 'y': self.pl_pos_y}

    def get_player_cell(self):
        return self.field[self.pl_pos_y][self.pl_pos_x]

    def move_player(self, target_cell: CELL):
        self.pl_pos_x, self.pl_pos_y = target_cell.x, target_cell.y
        if not self.is_final_size and type(target_cell) is not cell.CellExit:
            if self.pl_pos_x > self.max_x:
                self.max_x = self.pl_pos_x
                self.crop_field(Directions.left)
            elif self.pl_pos_x < self.min_x:
                self.min_x = self.pl_pos_x
                self.crop_field(Directions.right)

            if self.pl_pos_y > self.max_y:
                self.max_y = self.pl_pos_y
                self.crop_field(Directions.top)
            elif self.pl_pos_y < self.min_y:
                self.min_y = self.pl_pos_y
                self.crop_field(Directions.bottom)

            if self.max_x - self.min_x == self.size_x and self.max_y - self.min_y == self.size_y:
                self.is_final_size = True

    def crop_field(self, direction: Directions):
        match direction:
            case Directions.top:
                [self.update_cell_type(None, x, self.max_y - self.start_y) for x in range(len(self.field[0]))]
            case Directions.bottom:
                [self.update_cell_type(None, x, self.min_y - self.start_y - 1) for x in range(len(self.field[0]))]
            case Directions.left:
                [self.update_cell_type(None, self.max_x - self.start_x, y) for y in range(len(self.field))]
            case Directions.right:
                [self.update_cell_type(None, self.min_x - self.start_x - 1, y) for y in range(len(self.field))]

    def update_cell_type(self, new_type: Type[CELL] | None, pos_x: int, pos_y: int,
                         direction: Directions = None):
        if new_type is None:
            if self.field[pos_y][pos_x] is None or type(self.field[pos_y][pos_x]) is cell.CellExit:
                return
            self.field[pos_y][pos_x] = None
            return

        if new_type is cell.CellExit:
            self._create_exit(direction, self.field[pos_y][pos_x])
            return

        walls = self.field[pos_y][pos_x].walls
        self.field[pos_y][pos_x] = new_type(pos_x, pos_y) if not direction else cell.CellRiver(pos_x, pos_y, direction)
        self.field[pos_y][pos_x].walls = copy(walls)

        if direction:
            self.add_wall(self.field[pos_y][pos_x], direction, wall.WallEmpty)
        try:
            self.remaining_unique_obj_types.remove(new_type)
        except ValueError:
            pass

    def _create_exit(self, direction: Directions, current_cell: cell.Cell) -> None:
        """

        :param direction: direction of exit wall
        :param current_cell: position of cell which neighbour`s to exit
        :raises UnreachableState: if location for exit cell is not Unknown or None
        """
        target_cell = self.get_neighbour_cell(current_cell, direction)
        if type(target_cell) is cell.CellExit:
            return
        if type(target_cell) is not UnknownCell and target_cell is not None:
            raise UnreachableState()
        cell_exit = cell.CellExit(*direction.calc(current_cell.x, current_cell.y), -direction)
        for dir_ in Directions:
            if dir_ is -direction:
                continue
            neighbour_cell = self.get_neighbour_cell(cell_exit, dir_)
            if neighbour_cell:
                if type(neighbour_cell) is cell.CellExit:
                    continue
                self._update_wall(neighbour_cell, dir_, wall.WallOuter)
        current_cell.add_wall(direction, wall.WallExit())
        self.field[cell_exit.y][cell_exit.x] = cell_exit

    def add_wall(self, current_cell: CELL, direction: Directions, wall_type: Type[wall.WallEmpty],
                 neighbour_wall_type: Type[wall.WallEmpty] | None = None):
        current_cell.add_wall(direction, wall_type())
        neighbour = self.get_neighbour_cell(current_cell, direction)
        if neighbour:
            if neighbour_wall_type is None:
                neighbour_wall_type = wall_type
            self._update_wall(neighbour, direction, neighbour_wall_type)

    def _update_wall(self, target_cell: CELL, direction: Directions, wall_type):
        self.field[target_cell.y][target_cell.x] = copy(self.field[target_cell.y][target_cell.x])
        self.field[target_cell.y][target_cell.x].walls = copy(self.field[target_cell.y][target_cell.x].walls)
        self.field[target_cell.y][target_cell.x].add_wall(-direction, wall_type())

    def get_neighbour_cell(self, current_cell: CELL, direction: Directions):
        x, y = direction.calc(current_cell.x, current_cell.y)
        try:
            return self.field[y][x]
        except IndexError:
            return None

    def remove_leaf(self, leaf):
        self.next_states.remove(leaf)
        if not self.next_states and self.parent:
            self.parent.remove_leaf(self)

    def remove(self):
        self.parent.remove_leaf(self)

    def set_parent(self, node):
        self.parent = node

    def add_modified_leaf(self, target_cell: CELL, new_type: Type[CELL], direction: Directions = None):
        self.next_states.append(self.get_modified_copy(target_cell, new_type, direction))

    def get_modified_copy(self, target_cell: CELL, new_type: Type[CELL], direction: Directions = None):
        new_state = FieldState([copy(row) for row in self.field], self.pl_pos_x, self.pl_pos_y,
                               self, copy(self.remaining_unique_obj_types),
                               self.min_x, self.max_x, self.min_y, self.max_y,
                               self.size_x, self.size_y, self.start_x, self.start_y, self.is_final_size)
        new_state.update_cell_type(new_type, target_cell.x, target_cell.y, direction)
        if new_state.pl_pos_x != target_cell.x or new_state.pl_pos_y != target_cell.y:
            new_state.move_player(target_cell)
        return new_state

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
            self.add_wall(current_cell, direction, wall.WallEmpty)
        else:
            if current_cell.walls[direction].breakable and type(current_cell.walls[direction]) is not UnknownWall:
                raise UnreachableState()
            if type(current_cell.walls[direction]) is UnknownWall:
                self.add_wall(current_cell, direction, UnbreakableWall)

        self._pass_processor(direction, response)

    def _pass_processor(self, direction: Directions | None, response: dict):
        type_cell_turn_end: Type[cell.Cell] = response.get('type_cell_at_end_of_turn')
        cell_treasures_amount: int = response.get('cell_treasures_amount')
        type_out_treasure: TreasureTypes | None = response.get('type_out_treasure')

        current_cell = self.get_player_cell()
        if type(current_cell) is not cell.CellRiver:
            return  # todo add cell mechanics activator
        end_cell = self.get_neighbour_cell(current_cell, current_cell.direction)
        if type(end_cell) not in [type_cell_turn_end, UnknownCell]:
            raise UnreachableState()
        if type(end_cell) is type_cell_turn_end:
            neighbour_cell = self.get_neighbour_cell(current_cell, current_cell.direction)
            self.move_player(neighbour_cell)
        elif type_cell_turn_end is cell.CellRiver:
            self._calc_possible_river_trajectories(
                end_cell, type_cell_turn_end, type_cell_turn_end, False, current_cell.direction)
        elif type_cell_turn_end is cell.CellRiverMouth:
            self.update_cell_type(type_cell_turn_end, end_cell.x, end_cell.y)
            self.move_player(end_cell)
        else:
            raise UnreachableState()

    def _movement_processor(self, direction: Directions, response: dict):
        is_diff_cells: bool = response.get('diff_cells')
        type_cell_turn_end: Type[cell.Cell] = response.get('type_cell_at_end_of_turn')
        type_cell_after_wall_check: Type[cell.Cell] = response.get('type_cell_after_wall_check')
        is_wall_passed: bool = response.get('wall_passed')
        wall_type: Type[wall.WallEmpty] | None = response.get('wall_type')
        # todo учесть что это не обязательно настоящий тип стены
        cell_treasures_amount: int = response.get('cell_treasures_amount')
        type_out_treasure: TreasureTypes | None = response.get('type_out_treasure')

        start_cell = self.get_player_cell()
        new_cell = self.get_neighbour_cell(start_cell, direction)
        if not is_wall_passed:
            self.add_wall(start_cell, direction, wall_type)
            if new_cell:
                if type(new_cell) is cell.CellRiver and new_cell.direction is -direction:
                    raise UnreachableState()
                if type(start_cell) is cell.CellRiver and start_cell.direction is direction:
                    raise UnreachableState()

            new_cell = start_cell
            direction = -direction
        elif type_cell_turn_end is not cell.CellExit and type(start_cell) is not cell.CellExit:
            self.add_wall(start_cell, direction, wall.WallEmpty)

        # хотим пройти в выход, но он еще не создан
        if type_cell_turn_end is cell.CellExit and type(new_cell) is not cell.CellExit:
            self.update_cell_type(cell.CellExit, start_cell.x, start_cell.y, direction)
            new_cell = self.get_neighbour_cell(start_cell, direction)

        #  попытка сходить за пределы карты - значит всю ветку можно удалить
        if new_cell is None:
            raise UnreachableState()

        #  попытка изменить значение уже известной клетки
        if type(new_cell) not in [UnknownCell, type_cell_after_wall_check]:
            raise UnreachableState()

        #  перемещение в указанную сторону не противоречит известному полю
        if type_cell_after_wall_check is not cell.CellRiver:
            if type(new_cell) is UnknownCell:
                # todo добавить проверку для уникальных объектов (домики, клады и тп)
                self.update_cell_type(type_cell_after_wall_check, new_cell.x, new_cell.y)
            self.move_player(new_cell)
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
            # todo добавить проверку для уникальных объектов (домики, клады и тп)
            self.update_cell_type(type_cell_turn_end, self.pl_pos_x, self.pl_pos_y)
        else:
            player_cell = self.get_player_cell()
            possible_directions = self.get_possible_river_directions(player_cell)
            [self.add_modified_leaf(player_cell, type_cell_turn_end, dir_) for dir_ in possible_directions]

    def _calc_possible_river_trajectories(
            self, current_cell: CELL,
            type_cell_after_wall_check: Type[CELL],
            type_cell_turn_end: Type[CELL], is_diff_cells: bool, turn_direction: Directions):
        # ... , река, ...
        if type_cell_after_wall_check is cell.CellRiver and not is_diff_cells:
            if type(current_cell) not in [UnknownCell, cell.CellRiver]:
                raise UnreachableState()
            possible_river_dirs = self.get_possible_river_directions(current_cell, turn_direction)
            if not possible_river_dirs:
                raise UnreachableState()

            if type(current_cell) is UnknownCell:
                for direction in possible_river_dirs:
                    self.add_modified_leaf(current_cell, type_cell_after_wall_check, direction)
                return
            elif type(current_cell) is cell.CellRiver and current_cell.direction in possible_river_dirs:
                if self.get_player_cell() != current_cell:
                    self.move_player(current_cell)
                return
            raise UnreachableState()

        # ... , река-река / река-устье, ...

        # все варианты течения первой клетки
        new_states = self.get_possible_leafs(current_cell, turn_direction, washed=True)

        if type_cell_turn_end is not cell.CellRiverMouth:
            # все варианты течения второй клетки
            new_states2: list[FieldState] = []
            for new_state in new_states:
                riv_dir = new_state.get_player_cell().direction
                new_states2 += new_state.get_possible_leafs(
                    new_state.get_neighbour_cell(new_state.get_player_cell(), riv_dir), riv_dir)
            final_states: list[FieldState] = []
            for new_state in new_states2:
                riv_dir = new_state.get_player_cell().direction
                final_states += new_state.get_possible_leafs(
                    new_state.get_neighbour_cell(new_state.get_player_cell(), riv_dir), riv_dir)
            if not final_states:
                raise UnreachableState()
            if not (len(final_states) == 1 and final_states[0] is self):
                [state.set_parent(self) for state in final_states]
                self.next_states = final_states
            return
        else:  # смыло до устья
            final_states: list[FieldState] = []
            new_states2: list[FieldState] = []
            for new_state in new_states:
                riv_dir = new_state.get_player_cell().direction
                current_cell = new_state.get_neighbour_cell(new_state.get_player_cell(), riv_dir)
                if type(current_cell) is cell.CellRiverMouth:
                    new_state.move_player(current_cell)
                    final_states.append(new_state)
                else:
                    new_states2 += new_state.get_possible_leafs(current_cell, riv_dir)
                    if type(current_cell) is UnknownCell:
                        final_states.append(new_state.get_modified_copy(current_cell, type_cell_turn_end))

            for new_state in new_states2:
                riv_dir = new_state.get_player_cell().direction
                current_cell = new_state.get_neighbour_cell(new_state.get_player_cell(), riv_dir)
                if type(current_cell) is cell.CellRiverMouth:
                    new_state.move_player(current_cell)
                    final_states.append(new_state)
                else:
                    final_states.append(new_state.get_modified_copy(current_cell, type_cell_turn_end))
            if not final_states:
                raise UnreachableState()
            if not (len(final_states) == 1 and final_states[0] is self):
                [state.set_parent(self) for state in final_states]
                self.next_states = final_states
            return

    def get_possible_leafs(
            self, current_cell: CELL, turn_direction: Directions = None, is_final: bool = False,
            washed: bool = False, next_cell_is_mouth: bool = False):
        possible_river_dirs = self.get_possible_river_directions(current_cell, turn_direction, washed, next_cell_is_mouth)
        if type(current_cell) is UnknownCell:
            leaves = [self.get_modified_copy(current_cell, cell.CellRiver, direction)
                      for direction in possible_river_dirs]
            return leaves
        elif type(current_cell) is cell.CellRiver and current_cell.direction in possible_river_dirs:
            self.move_player(current_cell)
            return [self]
        else:
            raise UnreachableState()

    def get_possible_river_directions(self, river_cell: CELL, turn_direction: Directions = None,
                                      washed: bool = False, next_cell_is_mouth: bool = False) -> list[Directions]:
        dirs = []

        if not washed and turn_direction:
            prev_cell = self.get_neighbour_cell(river_cell, -turn_direction)
            if type(prev_cell) is cell.CellRiverMouth or (
                    type(prev_cell) is cell.CellRiver and prev_cell.direction is not turn_direction):
                if not self.has_known_input_river(prev_cell, -turn_direction):
                    return [-turn_direction]
                else:
                    return []

        for direction in Directions:
            # река не может течь в стену
            if type(river_cell.walls[direction]) not in [wall.WallEmpty, UnknownWall]:
                continue
            neighbour_cell = self.get_neighbour_cell(river_cell, direction)
            if neighbour_cell is None:
                continue

            # река не может течь в сушу
            if type(neighbour_cell) not in [cell.CellRiver, cell.CellRiverMouth, UnknownCell]:
                continue

            # реки не могут течь друг в друга
            if type(neighbour_cell) is cell.CellRiver and neighbour_cell.direction is -direction:
                continue

            # река не имеет развилок
            if self.has_known_input_river(neighbour_cell, direction):
                continue

            if type(neighbour_cell) is cell.CellRiverMouth and self.is_the_only_allowed_dir(neighbour_cell, direction):
                return [direction]

            # нет стены между соседом, сосед  - река / устье / неизвестная_клетка, в соседа ничего не втекает

            # если смыло, то река не может течь в клетку откуда пришли
            if washed and direction is -turn_direction:
                continue

            dirs.append(direction)
        return dirs

    def has_known_input_river(self, target_cell: CELL, dir_: Directions) -> bool:
        """

        :param target_cell: клетка для которой проверяем
        :param dir_: направление по которому пришли
        :return: True if has known input river
        """
        for direction in Directions:
            if direction is -dir_:
                continue
            neighbour_cell = self.get_neighbour_cell(target_cell, direction)
            if type(neighbour_cell) is cell.CellRiver and neighbour_cell.direction is -direction:
                return True

    def is_the_only_allowed_dir(self, target_cell: CELL, dir_: Directions) -> bool:
        """

        :param target_cell: клетка для которой проверяем
        :param dir_: направление по которому пришли
        :return: True if target cell have only 1 possible direction to input
        """
        for direction in Directions:
            if direction is -dir_:
                continue
            neighbour_cell = self.get_neighbour_cell(target_cell, direction)
            if (type(neighbour_cell) is cell.CellRiver and neighbour_cell.direction is -direction) or \
                    type(neighbour_cell) is UnknownCell:
                return False
        return True
