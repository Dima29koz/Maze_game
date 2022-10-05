from copy import copy
from typing import Type

from GameEngine.field import cell, wall
from GameEngine.globalEnv.enums import Directions, Actions, TreasureTypes
from GameEngine.globalEnv.types import Position

from bots_ai.field_handler.graph_builder import GraphBuilder
from bots_ai.exceptions import UnreachableState
from bots_ai.field_handler.field_obj import UnknownCell, UnknownWall, UnbreakableWall, PossibleExit
from bots_ai.field_handler.grid import Grid, CELL, WALL
from bots_ai.rules_preprocessor import RulesPreprocessor


class FieldState:
    """
    contains current field state known by player
    """

    def __init__(self, field: Grid,
                 remaining_obj_amount: dict[Type[cell.CELL], int],
                 players_positions: dict[str, Position | None],
                 preprocessed_rules: RulesPreprocessor,
                 is_real_spawn: bool = False,
                 current_player: str = ''):
        self.field = field
        self.players_positions = players_positions
        self.remaining_obj_amount = remaining_obj_amount
        self.is_real_spawn = is_real_spawn
        self.preprocessed_rules = preprocessed_rules

        self.current_player: str = current_player

        self.is_real = False  # todo only for testing

    def get_current_data(self):
        return self.field.get_field(), self.players_positions

    def get_player_cell(self) -> CELL:
        return self.field.get_cell(self.players_positions.get(self.current_player))

    def get_player_pos(self, player_name: str = None) -> Position | None:
        if not player_name:
            player_name = self.current_player
        return self.players_positions.get(player_name)

    def process_action(self, current_player: str,
                       action: Actions,
                       direction: Directions | None,
                       response: dict) -> list['FieldState']:
        if not self.players_positions.get(current_player):
            return []
        self.current_player = current_player

        match action:
            case Actions.swap_treasure:
                return self._treasure_swap_processor(response)
            case Actions.shoot_bow:
                return self._shooting_processor(direction, response)
            case Actions.throw_bomb:
                return self._bomb_throw_processor(direction, response)
            case Actions.skip:
                return self._pass_processor(response)
            case Actions.move:
                return self._movement_processor(direction, response)
            case Actions.info:
                return self._info_processor(response)

    def copy(self, player_name: str = None, position: Position = None) -> 'FieldState':
        return FieldState(
            self.field.copy(),
            self.remaining_obj_amount.copy(),
            self.players_positions.copy() if not position else self.update_player_position(player_name, position),
            self.preprocessed_rules,
            self.is_real_spawn,
            self.current_player)

    def update_player_position(self, player_name: str, position: Position) -> dict[str, Position | None]:
        pl_positions = self.players_positions.copy()
        pl_positions[player_name] = position
        return pl_positions

    def get_graph(self, player_name: str):
        current_pl_cell = self.field.get_cell(self.get_player_pos(player_name))
        return GraphBuilder(self.field, current_pl_cell)

    def _move_player(self, position: Position):
        self.players_positions[self.current_player] = position

    def _update_cell_type(self, new_type: Type[CELL], position: Position, direction: Directions = None):
        target_cell = self.field.get_cell(position)
        if type(target_cell) is not cell.NoneCell and new_type not in [cell.CellRiverMouth, cell.CellRiver]:
            if self.field.has_known_input_river(target_cell.position, direction, ignore_dir=True):
                raise UnreachableState()
        if type(target_cell) is not cell.NoneCell and new_type is not cell.CellRiver:
            if self.field.is_cause_of_isolated_mouth(target_cell.position):
                raise UnreachableState()

        if new_type is cell.NoneCell:
            if type(target_cell) is cell.NoneCell or type(target_cell) is cell.CellExit:
                return
            self.field.set_cell(cell.NoneCell(position), position)
            return

        if new_type is cell.CellExit:
            if type(target_cell) not in self.preprocessed_rules.exit_location:
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
            new_type(position) if not direction else cell.CellRiver(position, direction),
            position)
        self.field.set_walls(position, copy(walls))

        if direction:
            self.field.add_wall(position, direction, wall.WallEmpty)

    def _get_modified_copy(self, position: Position, new_type: Type[CELL], direction: Directions = None) -> 'FieldState':
        new_state = self.copy()
        new_state._update_cell_type(new_type, position, direction)
        if new_state.players_positions.get(self.current_player) != position:
            new_state._move_player(position)
        return new_state

    def _treasure_info_processor(self, response: dict, next_states: list['FieldState']):
        cell_treasures_amount: int = response.get('cell_treasures_amount')
        type_out_treasure: TreasureTypes | None = response.get('type_out_treasure')
        target_states = [self] if not next_states else next_states
        for state in target_states:
            pass
        return next_states

    def _treasure_swap_processor(self, response: dict) -> list['FieldState']:
        had_treasure: bool = response.get('had_treasure')  # был ли в руках клад до смены
        return []  # todo

    def _shooting_processor(self, direction: Directions, response: dict) -> list['FieldState']:
        is_hit: bool = response.get('hit')
        dmg_pls: list[str] = response.get('dmg_pls')
        dead_pls: list[str] = response.get('dead_pls')
        drop_pls: list[str] = response.get('drop_pls')

        #  todo add logic here

        return self._pass_processor(response)

    def _bomb_throw_processor(self, direction: Directions, response: dict) -> list['FieldState']:
        is_destroyed: bool = response.get('destroyed')

        current_cell = self.get_player_cell()
        if is_destroyed:
            if not current_cell.walls[direction].breakable:
                raise UnreachableState()
            self.field.add_wall(current_cell.position, direction, wall.WallEmpty)
        else:
            if current_cell.walls[direction].breakable and type(current_cell.walls[direction]) is not UnknownWall:
                raise UnreachableState()
            if type(current_cell.walls[direction]) is UnknownWall:
                self.field.add_wall(current_cell.position, direction, UnbreakableWall)

        return self._pass_processor(response)

    def _pass_processor(self, response: dict) -> list['FieldState']:
        type_cell_turn_end: Type[cell.CELL] = response.get('type_cell_at_end_of_turn')

        next_states = []

        current_cell = self.get_player_cell()
        if type(current_cell) is cell.CellRiver:
            end_cell = self.field.get_neighbour_cell(current_cell.position, current_cell.direction)
            if type(end_cell) not in [type_cell_turn_end, UnknownCell]:
                raise UnreachableState()
            if type(end_cell) is type_cell_turn_end:
                self._move_player(end_cell.position)
            elif type_cell_turn_end is cell.CellRiver:
                next_states = self._calc_possible_river_trajectories(
                    end_cell, type_cell_turn_end, type_cell_turn_end, False, current_cell.direction)
            elif type_cell_turn_end is cell.CellRiverMouth:
                self._update_cell_type(type_cell_turn_end, end_cell.position)
                self._move_player(end_cell.position)
            else:
                raise UnreachableState()

        return self._treasure_info_processor(response, next_states)

    def _movement_processor(self, turn_direction: Directions, response: dict) -> list['FieldState']:
        is_diff_cells: bool = response.get('diff_cells')
        type_cell_turn_end: Type[cell.CELL] = response.get('type_cell_at_end_of_turn')
        type_cell_after_wall_check: Type[cell.CELL] = response.get('type_cell_after_wall_check')
        is_wall_passed: bool = response.get('wall_passed')
        wall_type: Type[WALL] | None = response.get('wall_type')
        # todo учесть что это не обязательно настоящий тип стены

        next_states = []

        #  потрогать стену в направлении хода
        new_cell, turn_direction = self._wall_check_handler(
            turn_direction, type_cell_turn_end, is_wall_passed, wall_type)

        #  попытка сходить за пределы карты - значит всю ветку можно удалить
        if type(new_cell) is cell.NoneCell:
            raise UnreachableState()

        #  попытка изменить значение уже известной клетки
        if type(new_cell) not in [UnknownCell, type_cell_after_wall_check]:
            raise UnreachableState()

        #  перемещение в указанную сторону не противоречит известному полю
        if type_cell_after_wall_check is not cell.CellRiver:
            if type(new_cell) is UnknownCell:
                self._update_cell_type(type_cell_after_wall_check, new_cell.position)
            self._move_player(new_cell.position)

        # ... , река-река / река-устье / река, ...
        else:
            next_states = self._calc_possible_river_trajectories(
                new_cell, type_cell_after_wall_check, type_cell_turn_end, is_diff_cells, turn_direction)

        return self._treasure_info_processor(response, next_states)

    def _info_processor(self, response: dict) -> list['FieldState']:
        type_cell_turn_end: Type[cell.CELL] = response.get('type_cell_at_end_of_turn')
        next_states = []
        if type_cell_turn_end is not cell.CellRiver:
            self._update_cell_type(type_cell_turn_end, self.players_positions.get(self.current_player))
        else:
            player_cell = self.get_player_cell()
            possible_directions = self.field.get_possible_river_directions(player_cell)
            for dir_ in possible_directions:
                next_states.append(self._get_modified_copy(player_cell.position, type_cell_turn_end, dir_))

        return self._treasure_info_processor(response, next_states)

    def _wall_check_handler(self, turn_direction: Directions, type_cell_turn_end: Type[cell.CELL],
                            is_wall_passed: bool, wall_type: Type[WALL] | None):
        start_cell = self.get_player_cell()
        new_cell = self.field.get_neighbour_cell(start_cell.position, turn_direction)
        if not is_wall_passed:
            self._wall_bounce_handler(new_cell, start_cell, turn_direction, wall_type)
            new_cell = start_cell
            turn_direction = -turn_direction

        elif type_cell_turn_end is not cell.CellExit and type(start_cell) is not cell.CellExit:
            self.field.add_wall(start_cell.position, turn_direction, wall.WallEmpty)

        # хотим пройти в выход, но он еще не создан
        if type_cell_turn_end is cell.CellExit and type(new_cell) is not cell.CellExit:
            self._update_cell_type(cell.CellExit, new_cell.position, -turn_direction)
            new_cell = self.field.get_cell(new_cell.position)
        return new_cell, turn_direction

    def _wall_bounce_handler(self, new_cell: CELL | None, start_cell: CELL, turn_direction: Directions,
                             wall_type: Type[WALL]):
        if not new_cell:
            return
        if type(start_cell) is cell.CellExit:
            return
        if type(new_cell) is cell.CellRiver and new_cell.direction is -turn_direction:
            raise UnreachableState()
        if type(start_cell) is cell.CellRiver and start_cell.direction is turn_direction:
            raise UnreachableState()
        if type(new_cell) in [cell.NoneCell, PossibleExit]:
            wall_type = wall.WallOuter
            self._update_cell_type(cell.NoneCell, new_cell.position)
        self.field.add_wall(start_cell.position, turn_direction, wall_type)

    def _calc_possible_river_trajectories(
            self, current_cell: UnknownCell | cell.CellRiver,
            type_cell_after_wall_check: Type[cell.CellRiver | cell.CellRiverMouth],
            type_cell_turn_end: Type[cell.CellRiver | cell.CellRiverMouth],
            is_diff_cells: bool, turn_direction: Directions):
        # река-река: type_cell_after_wall_check == river, type_cell_turn_end == river, is_diff_cells = True
        # река-устье: type_cell_after_wall_check == river, type_cell_turn_end == mouth, is_diff_cells = True
        # река: type_cell_after_wall_check == river, type_cell_turn_end == river, is_diff_cells = False

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
                        new_state.field.get_neighbour_cell(new_state.get_player_pos(), riv_dir), riv_dir)
                except UnreachableState:
                    pass
            final_states: list[FieldState] = []
            for new_state in new_states2:
                riv_dir = new_state.get_player_cell().direction
                try:
                    final_states += new_state._get_possible_leaves(
                        new_state.field.get_neighbour_cell(new_state.get_player_pos(), riv_dir), riv_dir)
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
                current_cell = new_state.field.get_neighbour_cell(new_state.get_player_pos(), riv_dir)
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
                            final_states.append(new_state._get_modified_copy(current_cell.position, type_cell_turn_end))
                        except UnreachableState:
                            pass

            for new_state in new_states2:
                riv_dir = new_state.get_player_cell().direction
                current_cell = new_state.field.get_neighbour_cell(new_state.get_player_pos(), riv_dir)
                if type(current_cell) is cell.CellRiverMouth:
                    new_state._move_player(current_cell.position)
                    final_states.append(new_state)
                else:
                    try:
                        final_states.append(new_state._get_modified_copy(current_cell.position, type_cell_turn_end))
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
            prev_cell = self.field.get_neighbour_cell(current_cell.position, -turn_direction)
            if type(prev_cell) is cell.CellRiver and prev_cell.direction is turn_direction:
                raise UnreachableState()

        possible_river_dirs = self.field.get_possible_river_directions(current_cell, turn_direction, washed)
        if not possible_river_dirs:
            raise UnreachableState()

        if type(current_cell) is UnknownCell:
            leaves = [self._get_modified_copy(current_cell.position, cell.CellRiver, direction)
                      for direction in possible_river_dirs]
            return leaves
        elif type(current_cell) is cell.CellRiver and current_cell.direction in possible_river_dirs:
            self._move_player(current_cell.position)
            return [self]
        else:
            raise UnreachableState()

    def merge_with(self, other_state: 'FieldState', other_player: str):
        self.field.merge_with(other_state.field, self.remaining_obj_amount)
        self.players_positions[other_player] = other_state.get_player_pos(other_player)
        return self
