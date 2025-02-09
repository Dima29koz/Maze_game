from copy import copy
from typing import Type

from .common_data import CommonData
from .field_obj import (
    UnknownCell, UnknownWall, UnbreakableWall,
    PossibleExit, CellRiver, NoneCell,
    CellRiverMouth, CellExit, CELL
)
from .grid import Grid, WALL
from ..exceptions import UnreachableState, MergingError
from ...game_engine.field import wall
from ...game_engine.global_env.enums import Directions, Actions, TreasureTypes
from ...game_engine.global_env.types import Position


class FieldState:
    """
    contains current field state known by player
    """

    def __init__(self, field: Grid,
                 remaining_obj_amount: dict[Type[CELL], int],
                 players_positions: dict[str, Position | None],
                 common_data: CommonData,
                 treasures_positions: list[Position],
                 current_player: str = ''):
        self.field = field
        self.players_positions = players_positions
        self.treasures_positions = treasures_positions
        self.remaining_obj_amount = remaining_obj_amount
        self.common_data = common_data

        self.current_player: str = current_player

    def get_current_data(self):
        return self.field.get_field(), self.players_positions, self.treasures_positions

    def get_player_cell(self, player_name: str = None) -> CELL:
        if not player_name:
            player_name = self.current_player
        return self.field.get_cell(self.players_positions.get(player_name))

    def get_player_pos(self, player_name: str = None) -> Position | None:
        """

        :param player_name: target player name
        :return: position of target player if its known, else None
        """
        if not player_name:
            player_name = self.current_player
        return self.players_positions.get(player_name)

    def preprocess(self, current_player: str, allowed_abilities: dict[Actions, bool]):
        """
        add treasure into player cell if player is allowed to swap treasure

        :raise MergingError: if num treasures on map > treasures_amount
        """
        self.current_player = current_player
        if not self.get_player_pos():
            return
        if allowed_abilities.get(Actions.swap_treasure):
            self._merge_treasures([self.get_player_cell().position])

    def process_action(self, current_player: str,
                       action: Actions,
                       direction: Directions | None,
                       response: dict) -> list['FieldState']:
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

    def make_host_turn(self):
        new_treasures_pos = self.treasures_positions.copy()
        for treasure_position in self.treasures_positions:
            treasure_cell = self.field.get_cell(treasure_position)
            if type(treasure_cell) is CellRiver:
                new_cell = self.field.get_neighbour_cell(treasure_cell.position, treasure_cell.direction)
                new_treasures_pos.remove(treasure_position)
                if type(new_cell) is not UnknownCell:
                    new_treasures_pos.append(new_cell.position)
        self.treasures_positions = new_treasures_pos

    def copy(self, player_position: tuple[str, Position] = None) -> 'FieldState':
        return FieldState(
            self.field.copy(),
            self.remaining_obj_amount.copy(),
            self.players_positions.copy() if not player_position else self._update_player_position(player_position),
            self.common_data,
            self.treasures_positions.copy(),
            self.current_player)

    def _update_player_position(self, player_position: tuple[str, Position]) -> dict[str, Position | None]:
        pl_positions = self.players_positions.copy()
        pl_positions[player_position[0]] = player_position[1]
        return pl_positions

    def merge_with(self, other_state: 'FieldState'):
        self.field.merge_with(other_state.field, self.remaining_obj_amount)
        self._merge_players_positions(other_state.players_positions)
        self._merge_treasures(other_state.treasures_positions)
        return self

    def _move_player(self, position: Position):
        self.players_positions[self.current_player] = position

    def _update_cell_type(self, new_type: Type[CELL], position: Position, direction: Directions = None):
        target_cell = self.field.get_cell(position)
        if type(target_cell) is not NoneCell and new_type not in [CellRiverMouth, CellRiver]:
            if self.field.has_known_input_river(target_cell.position, direction, ignore_dir=True):
                raise UnreachableState()
        if type(target_cell) is not NoneCell and new_type is not CellRiver:
            if self.field.is_cause_of_isolated_mouth(target_cell.position):
                raise UnreachableState()

        if new_type is NoneCell:
            if type(target_cell) is NoneCell or type(target_cell) is CellExit:
                return
            self.field.set_cell(NoneCell(position), position)
            return

        if new_type is CellExit:
            if type(target_cell) not in self.common_data.exit_location:
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
            new_type(position) if not direction else CellRiver(position, direction),
            position)
        self.field.set_walls(position, copy(walls))

        if direction:
            self.field.add_wall(position, direction, wall.WallEmpty)

    def _get_modified_copy(self, position: Position,
                           new_type: Type[CELL], direction: Directions = None) -> 'FieldState':
        new_state = self.copy()
        new_state._update_cell_type(new_type, position, direction)
        if new_state.players_positions.get(self.current_player) != position:
            new_state._move_player(position)
        return new_state

    def _treasure_info_processor(self, response: dict, next_states: list['FieldState']):
        cell_treasures_amount: int = response.get('cell_treasures_amount')
        type_out_treasure: TreasureTypes | None = response.get('type_out_treasure')

        if not next_states:
            self._check_treasures_amount(cell_treasures_amount, self.get_player_cell().position)
            self._merge_treasures([self.get_player_cell().position for _ in range(cell_treasures_amount)])
            return [self]

        for state in next_states[::-1]:
            try:
                state._check_treasures_amount(cell_treasures_amount, state.get_player_cell().position)
                state._merge_treasures([state.get_player_cell().position for _ in range(cell_treasures_amount)])
            except (MergingError, UnreachableState):
                next_states.remove(state)
        if not next_states:
            raise UnreachableState()
        return next_states

    def _treasure_swap_processor(self, response: dict) -> list['FieldState']:
        if not self.get_player_pos():
            next_states = []
            if len(self.treasures_positions) < self.common_data.treasures_amount:
                next_states.append(self.copy())
            # сделать копию без каждого из кладов
            for treasure_pos in self.treasures_positions:
                next_state = self.copy()
                next_state.treasures_positions.remove(treasure_pos)
                # todo add logic here: position of player may be updated
                next_states.append(next_state)
            return next_states
        had_treasure: bool = response.get('had_treasure')  # был ли в руках клад до смены
        if not had_treasure:
            current_cell = self.get_player_cell()
            self.treasures_positions.remove(current_cell.position)
        # else при текущем способе хранения позиций кладов ничего не изменится
        return []  # todo

    def _shooting_processor(self, direction: Directions, response: dict) -> list['FieldState']:
        is_hit: bool = response.get('hit')
        dmg_pls: list[str] = response.get('dmg_pls')
        dead_pls: list[str] = response.get('dead_pls')
        drop_pls: list[str] = response.get('drop_pls')

        # todo add logic here (мог ли попасть / не попасть)
        # warning: position of current player might be None
        current_player_pos = self.get_player_pos()
        if current_player_pos:
            for damaged_player_name in dmg_pls:
                damaged_player_pos = self.get_player_pos(damaged_player_name)
                if damaged_player_pos:
                    self._check_shot_possibility(current_player_pos, damaged_player_pos, direction)

        if drop_pls:
            treasures_positions = []
            for player_name in drop_pls:
                other_pl_pos = self.get_player_pos(player_name)
                if other_pl_pos:
                    treasures_positions.append(other_pl_pos)
            self._merge_treasures(treasures_positions)

        return self._pass_processor(response)

    def _bomb_throw_processor(self, direction: Directions, response: dict) -> list['FieldState']:
        is_destroyed: bool = response.get('destroyed')

        if not self.get_player_pos():
            return []

        current_cell = self.get_player_cell()
        if is_destroyed:
            if not current_cell.walls[direction].breakable:
                raise UnreachableState()
            new_state = self.copy()
            if new_state.field.add_wall(current_cell.position, direction, wall.WallEmpty):
                return new_state._pass_processor(response)
        else:
            if current_cell.walls[direction].breakable and type(current_cell.walls[direction]) is not UnknownWall:
                raise UnreachableState()
            if type(current_cell.walls[direction]) is UnknownWall:
                new_state = self.copy()
                if new_state.field.add_wall(current_cell.position, direction, UnbreakableWall):
                    return new_state._pass_processor(response)

        return self._pass_processor(response)

    def _pass_processor(self, response: dict) -> list['FieldState']:
        type_cell_turn_end: Type[CELL] = response.get('type_cell_at_end_of_turn')

        if not self.get_player_pos():
            return []

        next_states = []

        current_cell = self.get_player_cell()
        if type(current_cell) is CellRiver:
            end_cell = self.field.get_neighbour_cell(current_cell.position, current_cell.direction)
            if type(end_cell) not in [type_cell_turn_end, UnknownCell]:
                raise UnreachableState()
            if type(end_cell) is type_cell_turn_end:
                self._move_player(end_cell.position)
            elif type_cell_turn_end is CellRiver:
                next_states = self._calc_possible_river_trajectories(
                    end_cell, type_cell_turn_end, type_cell_turn_end, False, current_cell.direction)
            elif type_cell_turn_end is CellRiverMouth:
                self._update_cell_type(type_cell_turn_end, end_cell.position)
                self._move_player(end_cell.position)
            else:
                raise UnreachableState()

        return self._treasure_info_processor(response, next_states)

    def _movement_processor(self, turn_direction: Directions, response: dict) -> list['FieldState']:
        is_diff_cells: bool = response.get('diff_cells')
        type_cell_turn_end: Type[CELL] = response.get('type_cell_at_end_of_turn')
        type_cell_after_wall_check: Type[CELL] = response.get('type_cell_after_wall_check')
        is_wall_passed: bool = response.get('wall_passed')
        wall_type: Type[WALL] | None = response.get('wall_type')
        # todo учесть что это не обязательно настоящий тип стены

        if not self.get_player_pos():
            return []

        next_states = []

        #  потрогать стену в направлении хода
        new_cell, turn_direction = self._wall_check_handler(
            turn_direction, type_cell_turn_end, is_wall_passed, wall_type)

        #  попытка сходить за пределы карты - значит всю ветку можно удалить
        if type(new_cell) is NoneCell:
            raise UnreachableState()

        #  попытка изменить значение уже известной клетки
        if type(new_cell) not in [UnknownCell, type_cell_after_wall_check]:
            raise UnreachableState()

        #  перемещение в указанную сторону не противоречит известному полю
        if type_cell_after_wall_check is not CellRiver:
            if type(new_cell) is UnknownCell:
                self._update_cell_type(type_cell_after_wall_check, new_cell.position)
            self._move_player(new_cell.position)

        # ... , река-река / река-устье / река, ...
        else:
            next_states = self._calc_possible_river_trajectories(
                new_cell, type_cell_after_wall_check, type_cell_turn_end, is_diff_cells, turn_direction)

        return self._treasure_info_processor(response, next_states)

    def _info_processor(self, response: dict) -> list['FieldState']:
        type_cell_turn_end: Type[CELL] = response.get('type_cell_at_end_of_turn')

        if not self.get_player_pos():
            return []

        next_states = []
        if type_cell_turn_end is not CellRiver:
            self._update_cell_type(type_cell_turn_end, self.players_positions.get(self.current_player))
        else:
            next_states = self._calc_possible_river_trajectories(
                self.get_player_cell(), type_cell_turn_end, type_cell_turn_end, False, None)

        return self._treasure_info_processor(response, next_states)

    @staticmethod
    def _check_shot_possibility(current_player_pos: Position,
                                damaged_player_pos: Position, shot_direction: Directions):
        if shot_direction in [Directions.top, Directions.bottom]:
            if current_player_pos.x != damaged_player_pos.x:
                raise UnreachableState()
        elif shot_direction in [Directions.right, Directions.left]:
            if current_player_pos.y != damaged_player_pos.y:
                raise UnreachableState()

    def _wall_check_handler(self, turn_direction: Directions, type_cell_turn_end: Type[CELL],
                            is_wall_passed: bool, wall_type: Type[WALL] | None):
        start_cell = self.get_player_cell()
        new_cell = self.field.get_neighbour_cell(start_cell.position, turn_direction)
        if not is_wall_passed:
            self._wall_bounce_handler(new_cell, start_cell, turn_direction, wall_type)
            new_cell = start_cell
            turn_direction = -turn_direction

        elif type_cell_turn_end is not CellExit and type(start_cell) is not CellExit:
            self.field.add_wall(start_cell.position, turn_direction, wall.WallEmpty)

        # хотим пройти в выход, но он еще не создан
        if type_cell_turn_end is CellExit and type(new_cell) is not CellExit:
            self._update_cell_type(CellExit, new_cell.position, -turn_direction)
            new_cell = self.field.get_cell(new_cell.position)
        return new_cell, turn_direction

    def _wall_bounce_handler(self, new_cell: CELL | None, start_cell: CELL, turn_direction: Directions,
                             wall_type: Type[WALL]):
        if not new_cell:
            return
        if type(start_cell) is CellExit:
            return
        if type(new_cell) is CellRiver and new_cell.direction is -turn_direction:
            raise UnreachableState()
        if type(start_cell) is CellRiver and start_cell.direction is turn_direction:
            raise UnreachableState()
        if type(new_cell) in [NoneCell, PossibleExit]:
            wall_type = wall.WallOuter
            self._update_cell_type(NoneCell, new_cell.position)
        self.field.add_wall(start_cell.position, turn_direction, wall_type)

    def _calc_possible_river_trajectories(
            self, current_cell: UnknownCell | CellRiver,
            type_cell_after_wall_check: Type[CellRiver | CellRiverMouth],
            type_cell_turn_end: Type[CellRiver | CellRiverMouth],
            is_diff_cells: bool,
            turn_direction: Directions | None) -> list['FieldState']:
        # река-река: type_cell_after_wall_check == river, type_cell_turn_end == river, is_diff_cells = True
        # река-устье: type_cell_after_wall_check == river, type_cell_turn_end == mouth, is_diff_cells = True
        # река: type_cell_after_wall_check == river, type_cell_turn_end == river, is_diff_cells = False

        # ... , река, ...
        if type_cell_after_wall_check is CellRiver and not is_diff_cells:
            final_states = self._get_possible_leaves(current_cell, turn_direction)
            if not final_states:
                raise UnreachableState()
            return final_states

        # ... , река-река / река-устье, ...

        # все варианты течения первой клетки
        new_states = self._get_possible_leaves(current_cell, turn_direction, washed=True)

        if type_cell_turn_end is not CellRiverMouth:
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
                if type(current_cell) is CellRiverMouth:
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
                if type(current_cell) is CellRiverMouth:
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
                             current_cell: UnknownCell | CellRiver,
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
            if type(prev_cell) is CellRiver and prev_cell.direction is turn_direction:
                raise UnreachableState()

        possible_river_dirs = self.field.get_possible_river_directions(current_cell, turn_direction, washed)
        if not possible_river_dirs:
            raise UnreachableState()

        if type(current_cell) is UnknownCell:
            leaves = [self._get_modified_copy(current_cell.position, CellRiver, direction)
                      for direction in possible_river_dirs]
            return leaves
        elif type(current_cell) is CellRiver and current_cell.direction in possible_river_dirs:
            self._move_player(current_cell.position)
            return [self]
        else:
            raise UnreachableState()

    def _merge_treasures(self, other_treasures: list[Position]):
        if not other_treasures:
            return
        d_treasures = self.treasures_positions.copy()
        d_other_treasures = other_treasures.copy()
        for treasure_pos in other_treasures:
            if treasure_pos in d_treasures:
                d_treasures.remove(treasure_pos)
                d_other_treasures.remove(treasure_pos)
        merged_treasures_pos = self.treasures_positions + d_other_treasures
        if len(merged_treasures_pos) + self.common_data.players_with_treasures > self.common_data.treasures_amount:
            raise MergingError()
        self.treasures_positions = merged_treasures_pos

    def _merge_players_positions(self, other_state_positions: dict[str, Position | None]):
        for player, position in self.players_positions.items():
            if position is None and other_state_positions[player]:
                self.players_positions[player] = other_state_positions[player]
            if position and other_state_positions[player] and position != other_state_positions[player]:
                raise MergingError

    def _check_treasures_amount(self, cell_treasures_amount: int, position: Position):
        tr_pos_amount = len([pos for pos in self.treasures_positions if pos == position])
        if tr_pos_amount > cell_treasures_amount:
            raise UnreachableState()
