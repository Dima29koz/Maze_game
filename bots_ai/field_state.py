from copy import copy
from typing import Type

from GameEngine.field import cell, wall
from GameEngine.globalEnv.enums import Directions, Actions, TreasureTypes
from GameEngine.globalEnv.types import Position

from bots_ai.exceptions import UnreachableState
from bots_ai.field_obj import UnknownCell, UnknownWall, UnbreakableWall
from bots_ai.grid import Grid, R_CELL, R_WALL, CELL, WALL


class FieldState:
    """
    contains current field state known by player
    """

    def __init__(self, field: Grid,
                 remaining_obj_amount: dict[Type[R_CELL], int],
                 enemy_compatibility: dict[str, bool],
                 players_positions: dict[str, Position | None],
                 is_real_spawn: bool = False,
                 parent: 'FieldState' = None, current_player: str = ''):
        self.field = field
        self.players_positions = players_positions
        self.remaining_obj_amount = remaining_obj_amount
        self.next_states: list[FieldState] = []
        self.parent: FieldState | None = parent
        self.is_real_spawn = is_real_spawn
        self.enemy_compatibility = enemy_compatibility

        self.current_player: str = current_player

        self.is_real = False  # todo only for testing

    def get_current_data(self):
        return self.field.get_field(), self.players_positions

    def get_player_cell(self):
        return self.field.get_cell(self.players_positions.get(self.current_player))

    def remove(self):
        self.parent._remove_leaf(self)

    def process_action(self, current_player: str, action: Actions, direction: Directions | None, response: dict):
        self.current_player = current_player
        try:
            match action:
                case Actions.swap_treasure:
                    self._treasure_swap_processor(response)
                case Actions.shoot_bow:
                    self._shooting_processor(direction, response)
                case Actions.throw_bomb:
                    self._bomb_throw_processor(direction, response)
                case Actions.skip:
                    self._pass_processor(response)
                case Actions.move:
                    self._movement_processor(direction, response)
                case Actions.info:
                    self._info_processor(response)
        except UnreachableState:
            self.remove()

    def copy(self, player_name: str = None, position: Position = None):
        return FieldState(
            self.field.copy(),
            self.remaining_obj_amount.copy(),
            self.enemy_compatibility.copy(),
            self.players_positions.copy() if not position else self.update_player_position(player_name, position),
            self.is_real_spawn,
            self, self.current_player)

    def update_player_position(self, player_name: str, position: Position):
        pl_positions = self.players_positions.copy()
        pl_positions[player_name] = position
        return pl_positions

    def update_compatibility(self, player_name: str, value: bool):
        self.enemy_compatibility[player_name] = value

    def check_compatibility(self):
        if True not in self.enemy_compatibility.values() and not self.is_real_spawn:
            self.remove()
            return False
        return True

    def _move_player(self, position: Position):
        self.players_positions[self.current_player] = position

    def _update_cell_type(self, new_type: Type[CELL] | None, position: Position, direction: Directions = None):
        target_cell = self.field.get_cell(position) if new_type is not cell.CellExit else \
            self.field.get_neighbour_cell(self.field.get_cell(position), direction)
        if target_cell is not None and new_type not in [cell.CellRiverMouth, cell.CellRiver]:
            if self.field.has_known_input_river(target_cell, direction, ignore_dir=True):
                raise UnreachableState()
        if target_cell is not None and new_type is not cell.CellRiver:
            if self.field.is_cause_of_isolated_mouth(target_cell):
                raise UnreachableState()

        if new_type is None:
            if target_cell is None or type(target_cell) is cell.CellExit:
                return
            self.field.set_cell(None, position)
            return

        if new_type is cell.CellExit:
            if type(target_cell) is not UnknownCell and target_cell is not None:
                raise UnreachableState()
            self.field.create_exit(direction, position)
            return

        # todo кажется надо убедиться что я не клоун, ибо а зачем обновлять тип известной клетки
        if type(target_cell) is UnknownCell:
            try:
                if self.remaining_obj_amount.get(new_type) == 0:
                    raise UnreachableState()
                self.remaining_obj_amount[new_type] -= 1
            except KeyError:
                pass

        walls = self.field.get_cell(position).walls
        self.field.set_cell(
            new_type(position.x, position.y) if not direction else cell.CellRiver(position.x, position.y, direction),
            position)
        self.field.set_walls(position, copy(walls))

        if direction:
            self.field.add_wall(self.field.get_cell(position), direction, wall.WallEmpty)

    def _remove_leaf(self, leaf: 'FieldState'):
        self.next_states.remove(leaf)
        if not self.next_states and self.parent:
            self.parent._remove_leaf(self)

    def _set_parent(self, parent: 'FieldState'):
        self.parent = parent

    def _add_modified_leaf(self, target_cell: CELL, new_type: Type[R_CELL], direction: Directions = None):
        self.next_states.append(self._get_modified_copy(target_cell, new_type, direction))

    def _get_modified_copy(self, target_cell: CELL, new_type: Type[CELL], direction: Directions = None):
        new_state = self.copy()
        new_state._update_cell_type(new_type, target_cell.position, direction)
        if new_state.players_positions.get(self.current_player) != target_cell.position:
            new_state._move_player(target_cell.position)
        return new_state

    def _treasure_swap_processor(self, response: dict):
        pass  # todo

    def _shooting_processor(self, direction: Directions, response: dict):
        is_hit: bool = response.get('hit')
        dmg_pls: list[str] = response.get('dmg_pls')
        dead_pls: list[str] = response.get('dead_pls')
        drop_pls: list[str] = response.get('drop_pls')

        #  todo add logic here

        self._pass_processor(response)

    def _bomb_throw_processor(self, direction: Directions, response: dict) -> None:
        is_destroyed: bool = response.get('destroyed')

        current_cell = self.get_player_cell()
        if is_destroyed:
            if not current_cell.walls[direction].breakable:
                raise UnreachableState()
            self.field.add_wall(current_cell, direction, wall.WallEmpty)
        else:
            if current_cell.walls[direction].breakable and type(current_cell.walls[direction]) is not UnknownWall:
                raise UnreachableState()
            if type(current_cell.walls[direction]) is UnknownWall:
                self.field.add_wall(current_cell, direction, UnbreakableWall)

        self._pass_processor(response)

    def _pass_processor(self, response: dict):
        type_cell_turn_end: Type[R_CELL] = response.get('type_cell_at_end_of_turn')
        cell_treasures_amount: int = response.get('cell_treasures_amount')
        type_out_treasure: TreasureTypes | None = response.get('type_out_treasure')

        current_cell = self.get_player_cell()
        if type(current_cell) is not cell.CellRiver:
            return  # todo add cell mechanics activator
        end_cell = self.field.get_neighbour_cell(current_cell, current_cell.direction)
        if type(end_cell) not in [type_cell_turn_end, UnknownCell]:
            raise UnreachableState()
        if type(end_cell) is type_cell_turn_end:
            neighbour_cell = self.field.get_neighbour_cell(current_cell, current_cell.direction)
            self._move_player(neighbour_cell.position)
        elif type_cell_turn_end is cell.CellRiver:
            final_states = self._calc_possible_river_trajectories(
                end_cell, type_cell_turn_end, type_cell_turn_end, False, current_cell.direction)
            if not (len(final_states) == 1 and final_states[0] is self):
                [state._set_parent(self) for state in final_states]
                self.next_states = final_states
        elif type_cell_turn_end is cell.CellRiverMouth:
            self._update_cell_type(type_cell_turn_end, end_cell.position)
            self._move_player(end_cell.position)
        else:
            raise UnreachableState()

    def _movement_processor(self, turn_direction: Directions, response: dict):
        is_diff_cells: bool = response.get('diff_cells')
        type_cell_turn_end: Type[R_CELL] = response.get('type_cell_at_end_of_turn')
        type_cell_after_wall_check: Type[R_CELL] = response.get('type_cell_after_wall_check')
        is_wall_passed: bool = response.get('wall_passed')
        wall_type: Type[WALL] | None = response.get('wall_type')
        # todo учесть что это не обязательно настоящий тип стены
        cell_treasures_amount: int = response.get('cell_treasures_amount')
        type_out_treasure: TreasureTypes | None = response.get('type_out_treasure')

        start_cell = self.get_player_cell()
        new_cell = self.field.get_neighbour_cell(start_cell, turn_direction)
        if not is_wall_passed:
            if new_cell:
                if type(new_cell) is cell.CellRiver and new_cell.direction is -turn_direction:
                    raise UnreachableState()
                if type(start_cell) is cell.CellRiver and start_cell.direction is turn_direction:
                    raise UnreachableState()
            self.field.add_wall(start_cell, turn_direction, wall_type)

            new_cell = start_cell
            turn_direction = -turn_direction
        elif type_cell_turn_end is not cell.CellExit and type(start_cell) is not cell.CellExit:
            self.field.add_wall(start_cell, turn_direction, wall.WallEmpty)

        # хотим пройти в выход, но он еще не создан
        if type_cell_turn_end is cell.CellExit and type(new_cell) is not cell.CellExit:
            self._update_cell_type(cell.CellExit, start_cell.position, turn_direction)
            new_cell = self.field.get_neighbour_cell(start_cell, turn_direction)

        #  попытка сходить за пределы карты - значит всю ветку можно удалить
        if new_cell is None:
            raise UnreachableState()

        #  попытка изменить значение уже известной клетки
        if type(new_cell) not in [UnknownCell, type_cell_after_wall_check]:
            raise UnreachableState()

        #  перемещение в указанную сторону не противоречит известному полю
        if type_cell_after_wall_check is not cell.CellRiver:
            if type(new_cell) is UnknownCell:
                self._update_cell_type(type_cell_after_wall_check, new_cell.position)
            self._move_player(new_cell.position)
            return

        # ... , река-река / река-устье / река, ...
        # река-река: type_cell_after_wall_check == river, type_cell_turn_end == river, is_diff_cells = True
        # река-устье: type_cell_after_wall_check == river, type_cell_turn_end == mouth, is_diff_cells = True
        # река: type_cell_after_wall_check == river, type_cell_turn_end == river, is_diff_cells = False

        final_states = self._calc_possible_river_trajectories(
            new_cell, type_cell_after_wall_check, type_cell_turn_end, is_diff_cells, turn_direction)
        if not (len(final_states) == 1 and final_states[0] is self):
            [state._set_parent(self) for state in final_states]
            self.next_states = final_states

    def _info_processor(self, response: dict):
        type_cell_turn_end: Type[R_CELL] = response.get('type_cell_at_end_of_turn')
        cell_treasures_amount: int = response.get('cell_treasures_amount')

        if type_cell_turn_end is not cell.CellRiver:
            self._update_cell_type(type_cell_turn_end, self.players_positions.get(self.current_player))
        else:
            player_cell = self.get_player_cell()
            possible_directions = self.field.get_possible_river_directions(player_cell)
            [self._add_modified_leaf(player_cell, type_cell_turn_end, dir_) for dir_ in possible_directions]

    def _calc_possible_river_trajectories(
            self, current_cell: UnknownCell | cell.CellRiver,
            type_cell_after_wall_check: Type[cell.CellRiver | cell.CellRiverMouth],
            type_cell_turn_end: Type[cell.CellRiver | cell.CellRiverMouth],
            is_diff_cells: bool, turn_direction: Directions):
        # ... , река, ...
        if type_cell_after_wall_check is cell.CellRiver and not is_diff_cells:
            final_states = self._get_possible_leaves(current_cell, turn_direction)
            if not final_states:
                raise UnreachableState()
            return final_states

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
                        new_state.field.get_neighbour_cell(new_state.get_player_cell(), riv_dir), riv_dir)
                except UnreachableState:
                    pass
            final_states: list[FieldState] = []
            for new_state in new_states2:
                riv_dir = new_state.get_player_cell().direction
                try:
                    final_states += new_state._get_possible_leaves(
                        new_state.field.get_neighbour_cell(new_state.get_player_cell(), riv_dir), riv_dir)
                except UnreachableState:
                    pass
            if not final_states:
                raise UnreachableState()
            return final_states
        else:  # смыло до устья
            final_states: list[FieldState] = []
            new_states2: list[FieldState] = []
            for new_state in new_states:
                riv_dir = new_state.get_player_cell().direction
                current_cell = new_state.field.get_neighbour_cell(new_state.get_player_cell(), riv_dir)
                if type(current_cell) is cell.CellRiverMouth:
                    new_state._move_player(current_cell.position)
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
                current_cell = new_state.field.get_neighbour_cell(new_state.get_player_cell(), riv_dir)
                if type(current_cell) is cell.CellRiverMouth:
                    new_state._move_player(current_cell.position)
                    final_states.append(new_state)
                else:
                    try:
                        final_states.append(new_state._get_modified_copy(current_cell, type_cell_turn_end))
                    except UnreachableState:
                        pass
            if not final_states:
                raise UnreachableState()
            return final_states

    def _get_possible_leaves(self,
                             current_cell: UnknownCell | cell.CellRiver,
                             turn_direction: Directions = None,
                             washed: bool = False):
        """

        :param current_cell: cell to be checked for possible directions
        :param turn_direction: direction of players turn
        :param washed: is player washed by river
        :return: list of new field states or modified current state
        :raises UnreachableState: If current cell can`t be river
        """

        if washed:
            prev_cell = self.field.get_neighbour_cell(current_cell, -turn_direction)
            if type(prev_cell) is cell.CellRiver and prev_cell.direction is turn_direction:
                raise UnreachableState()

        possible_river_dirs = self.field.get_possible_river_directions(current_cell, turn_direction, washed)
        if not possible_river_dirs:
            raise UnreachableState()

        if type(current_cell) is UnknownCell:
            leaves = [self._get_modified_copy(current_cell, cell.CellRiver, direction)
                      for direction in possible_river_dirs]
            return leaves
        elif type(current_cell) is cell.CellRiver and current_cell.direction in possible_river_dirs:
            self._move_player(current_cell.position)
            return [self]
        else:
            raise UnreachableState()

    def merge_with(self, pl_node: 'FieldState'):
        if self.field.merge_with(pl_node.field):
            return self
        return
