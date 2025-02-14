from typing import Type

from .common_data import CommonData
from .field_obj import BotCellTypes, BotCell, UnknownWall, UnbreakableWall
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
                 remaining_obj_amount: dict[BotCellTypes, int],
                 players_positions: dict[str, Position | None],
                 common_data: CommonData,
                 treasures_positions: list[Position]):
        self.field = field
        self.players_positions = players_positions
        self.treasures_positions = treasures_positions
        self.remaining_obj_amount = remaining_obj_amount
        self.common_data = common_data

    def get_current_data(self):
        return self.field.get_field(), self.players_positions, self.treasures_positions

    def get_player_cell(self, player_name: str) -> BotCell:
        return self.field.get_cell(self.players_positions.get(player_name))

    def get_player_pos(self, player_name: str) -> Position | None:
        """

        :param player_name: target player name
        :return: position of target player if its known, else None
        """
        return self.players_positions.get(player_name)

    def preprocess(self, player_name: str, allowed_abilities: dict[Actions, bool]):
        """
        add treasure into player cell if player is allowed to swap treasure

        :param player_name: active player for which to preprocess turn
        :param allowed_abilities: active player allowed abilities
        :raise MergingError: if num treasures on map > treasures_amount
        """
        player_position = self.get_player_pos(player_name)
        if not player_position:
            return
        if allowed_abilities.get(Actions.swap_treasure):
            self._merge_treasures([player_position])

    def process_action(self, current_player: str,
                       action: Actions,
                       direction: Directions | None,
                       response: dict) -> list['FieldState']:

        match action:
            case Actions.swap_treasure:
                return self._treasure_swap_processor(response, current_player)
            case Actions.shoot_bow:
                return self._shooting_processor(direction, response, current_player)
            case Actions.throw_bomb:
                return self._bomb_throw_processor(direction, response, current_player)
            case Actions.skip:
                return self._pass_processor(response, current_player)
            case Actions.move:
                return self._movement_processor(direction, response, current_player)
            case Actions.info:
                return self._info_processor(response, current_player)
            case _:
                raise RuntimeError(f'unknown action `{action}`')

    def make_host_turn(self):
        new_treasures_pos = self.treasures_positions.copy()
        for treasure_position in self.treasures_positions:
            treasure_cell = self.field.get_cell(treasure_position)
            if treasure_cell.type is BotCellTypes.CellRiver:
                new_cell = self.field.get_neighbour_cell(treasure_cell.position, treasure_cell.direction)
                new_treasures_pos.remove(treasure_position)
                if new_cell.type is not BotCellTypes.UnknownCell:
                    new_treasures_pos.append(new_cell.position)
        self.treasures_positions = new_treasures_pos

    def copy(self, player_position: tuple[str, Position] = None) -> 'FieldState':
        return FieldState(
            self.field.copy(),
            self.remaining_obj_amount.copy(),
            self.players_positions.copy() if not player_position else self._update_player_position(player_position),
            self.common_data,
            self.treasures_positions.copy()
        )

    def _update_player_position(self, player_position: tuple[str, Position]) -> dict[str, Position | None]:
        pl_positions = self.players_positions.copy()
        pl_positions[player_position[0]] = player_position[1]
        return pl_positions

    def merge_with(self, other_state: 'FieldState'):
        self.field.merge_with(other_state.field, self.remaining_obj_amount)
        self._merge_players_positions(other_state.players_positions)
        self._merge_treasures(other_state.treasures_positions)
        return self

    def _move_player(self, player_name: str, position: Position):
        self.players_positions[player_name] = position

    def _update_cell_type(self, new_type: BotCellTypes, position: Position, direction: Directions = None):
        target_cell_type = self.field.get_cell(position).type
        if target_cell_type is not BotCellTypes.NoneCell and new_type not in [BotCellTypes.CellRiverMouth,
                                                                              BotCellTypes.CellRiver]:
            if self.field.has_known_input_river(position, direction, ignore_dir=True):
                raise UnreachableState()
        if target_cell_type is not BotCellTypes.NoneCell and new_type is not BotCellTypes.CellRiver:
            if self.field.is_cause_of_isolated_mouth(position):
                raise UnreachableState()

        if new_type is BotCellTypes.NoneCell:
            if target_cell_type is BotCellTypes.NoneCell or target_cell_type is BotCellTypes.CellExit:
                return
            self.field.set_cell(position, BotCellTypes.NoneCell)
            return

        if new_type is BotCellTypes.CellExit:
            if target_cell_type not in self.common_data.exit_location:
                raise UnreachableState()
            self.field.create_exit(direction, position)
            return

        # todo кажется надо убедиться что я не клоун, ибо а зачем обновлять тип известной клетки
        if target_cell_type is BotCellTypes.UnknownCell:
            try:
                if self.remaining_obj_amount.get(new_type) == 0:
                    raise UnreachableState()
                self.remaining_obj_amount[new_type] -= 1
            except KeyError:
                pass

        walls = self.field.get_cell(position).walls.copy()
        self.field.set_cell(position, new_type, walls, direction)

        if direction:
            self.field.add_wall(position, direction, wall.WallEmpty)

    def _get_modified_copy(self,
                           position: Position,
                           new_type: BotCellTypes,
                           current_player: str,
                           direction: Directions = None) -> 'FieldState':
        new_state = self.copy()
        new_state._update_cell_type(new_type, position, direction)
        if new_state.players_positions.get(current_player) != position:
            new_state._move_player(current_player, position)
        return new_state

    def _treasure_info_processor(self, response: dict, next_states: list['FieldState'], current_player: str):
        cell_treasures_amount: int = response.get('cell_treasures_amount')
        type_out_treasure: TreasureTypes | None = response.get('type_out_treasure')

        if not next_states:
            self._check_treasures_amount(cell_treasures_amount, self.get_player_cell(current_player).position)
            self._merge_treasures([self.get_player_cell(current_player).position for _ in range(cell_treasures_amount)])
            return [self]

        for state in next_states[::-1]:
            try:
                state._check_treasures_amount(cell_treasures_amount, state.get_player_cell(current_player).position)
                state._merge_treasures(
                    [state.get_player_cell(current_player).position for _ in range(cell_treasures_amount)])
            except (MergingError, UnreachableState):
                next_states.remove(state)
        if not next_states:
            raise UnreachableState()
        return next_states

    def _treasure_swap_processor(self, response: dict, current_player: str) -> list['FieldState']:
        player_position = self.get_player_pos(current_player)
        if not player_position:
            next_states = []
            # todo add logic here: if player had treasure before swap
            if len(self.treasures_positions) < self.common_data.treasures_amount:
                next_states.append(self.copy())
            # сделать копию без каждого из кладов
            for treasure_pos in self.treasures_positions:
                next_state: FieldState = self.copy()
                next_state.treasures_positions.remove(treasure_pos)
                # todo add logic here: position of player may be updated
                next_states.append(next_state)
            return next_states

        had_treasure: bool = response.get('had_treasure')  # был ли в руках клад до смены
        if not had_treasure:
            self.treasures_positions.remove(player_position)
        # else при текущем способе хранения позиций кладов ничего не изменится
        return []  # todo

    def _shooting_processor(self, direction: Directions, response: dict, current_player: str) -> list['FieldState']:
        is_hit: bool = response.get('hit')
        dmg_pls: list[str] = response.get('dmg_pls')
        dead_pls: list[str] = response.get('dead_pls')
        drop_pls: list[str] = response.get('drop_pls')

        # todo add logic here (мог ли попасть / не попасть)
        # warning: position of current player might be None
        current_player_pos = self.get_player_pos(current_player)
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

        return self._pass_processor(response, current_player)

    def _bomb_throw_processor(self, direction: Directions, response: dict, current_player: str) -> list['FieldState']:
        is_destroyed: bool = response.get('destroyed')

        if not self.get_player_pos(current_player):
            return []

        current_cell = self.get_player_cell(current_player)
        affected_wall = current_cell.walls[direction]
        if is_destroyed:
            if not affected_wall.breakable:
                raise UnreachableState()
            new_state = self.copy()
            if new_state.field.add_wall(current_cell.position, direction, wall.WallEmpty):
                return new_state._pass_processor(response, current_player)
        else:
            if affected_wall.breakable and type(affected_wall) is not UnknownWall:
                raise UnreachableState()
            if type(affected_wall) is UnknownWall:
                new_state = self.copy()
                if new_state.field.add_wall(current_cell.position, direction, UnbreakableWall):
                    return new_state._pass_processor(response, current_player)

        return self._pass_processor(response, current_player)

    def _pass_processor(self, response: dict, current_player: str) -> list['FieldState']:
        type_cell_turn_end: BotCellTypes = response.get('type_cell_at_end_of_turn')

        if not self.get_player_pos(current_player):
            return []

        next_states = []

        current_cell = self.get_player_cell(current_player)
        if current_cell.type is BotCellTypes.CellRiver:
            end_cell = self.field.get_neighbour_cell(current_cell.position, current_cell.direction)
            if end_cell.type not in [type_cell_turn_end, BotCellTypes.UnknownCell]:
                raise UnreachableState()
            if end_cell.type is type_cell_turn_end:
                self._move_player(current_player, end_cell.position)
            elif type_cell_turn_end is BotCellTypes.CellRiver:
                next_states = self._calc_possible_river_trajectories(
                    end_cell, type_cell_turn_end, type_cell_turn_end, False, current_player, current_cell.direction)
            elif type_cell_turn_end is BotCellTypes.CellRiverMouth:
                self._update_cell_type(type_cell_turn_end, end_cell.position)
                self._move_player(current_player, end_cell.position)
            else:
                raise UnreachableState()

        return self._treasure_info_processor(response, next_states, current_player)

    def _movement_processor(self, turn_direction: Directions, response: dict, current_player: str) -> list[
        'FieldState']:
        is_diff_cells: bool = response.get('diff_cells')
        type_cell_turn_end: BotCellTypes = response.get('type_cell_at_end_of_turn')
        type_cell_after_wall_check: BotCellTypes = response.get('type_cell_after_wall_check')
        is_wall_passed: bool = response.get('wall_passed')
        wall_type: Type[WALL] | None = response.get('wall_type')
        # todo учесть что это не обязательно настоящий тип стены

        if not self.get_player_pos(current_player):
            return []

        next_states = []

        #  потрогать стену в направлении хода
        start_cell = self.get_player_cell(current_player)
        new_cell, turn_direction = self._wall_check_handler(start_cell,
                                                            turn_direction, type_cell_turn_end, is_wall_passed,
                                                            wall_type)

        #  попытка сходить за пределы карты - значит всю ветку можно удалить
        if new_cell.type is BotCellTypes.NoneCell:
            raise UnreachableState()

        #  попытка изменить значение уже известной клетки
        if new_cell.type not in [BotCellTypes.UnknownCell, type_cell_after_wall_check]:
            raise UnreachableState()

        #  перемещение в указанную сторону не противоречит известному полю
        if type_cell_after_wall_check is not BotCellTypes.CellRiver:
            if new_cell.type is BotCellTypes.UnknownCell:
                self._update_cell_type(type_cell_after_wall_check, new_cell.position)
            self._move_player(current_player, new_cell.position)

        # ... , река-река / река-устье / река, ...
        else:
            next_states = self._calc_possible_river_trajectories(
                new_cell, type_cell_after_wall_check, type_cell_turn_end, is_diff_cells, current_player, turn_direction)

        return self._treasure_info_processor(response, next_states, current_player)

    def _info_processor(self, response: dict, current_player: str) -> list['FieldState']:
        type_cell_turn_end: BotCellTypes = response.get('type_cell_at_end_of_turn')

        player_position = self.get_player_pos(current_player)
        if not player_position:
            return []

        next_states = []
        if type_cell_turn_end is not BotCellTypes.CellRiver:
            self._update_cell_type(type_cell_turn_end, player_position)
        else:
            next_states = self._calc_possible_river_trajectories(
                self.get_player_cell(current_player), type_cell_turn_end, type_cell_turn_end, False, current_player,
                None)

        return self._treasure_info_processor(response, next_states, current_player)

    @staticmethod
    def _check_shot_possibility(current_player_pos: Position,
                                damaged_player_pos: Position, shot_direction: Directions):
        if shot_direction in [Directions.top, Directions.bottom]:
            if current_player_pos.x != damaged_player_pos.x:
                raise UnreachableState()
        elif shot_direction in [Directions.right, Directions.left]:
            if current_player_pos.y != damaged_player_pos.y:
                raise UnreachableState()

    def _wall_check_handler(self, start_cell: BotCell, turn_direction: Directions, type_cell_turn_end: BotCellTypes,
                            is_wall_passed: bool, wall_type: Type[WALL] | None):

        new_cell = self.field.get_neighbour_cell(start_cell.position, turn_direction)
        if not is_wall_passed:
            self._wall_bounce_handler(new_cell, start_cell, turn_direction, wall_type)
            new_cell = start_cell
            turn_direction = -turn_direction

        elif type_cell_turn_end is not BotCellTypes.CellExit and start_cell.type is not BotCellTypes.CellExit:
            self.field.add_wall(start_cell.position, turn_direction, wall.WallEmpty)

        # хотим пройти в выход, но он еще не создан
        if type_cell_turn_end is BotCellTypes.CellExit and new_cell.type is not BotCellTypes.CellExit:
            self._update_cell_type(BotCellTypes.CellExit, new_cell.position, -turn_direction)
            new_cell = self.field.get_cell(new_cell.position)
        return new_cell, turn_direction

    def _wall_bounce_handler(self, new_cell: BotCell | None, start_cell: BotCell, turn_direction: Directions,
                             wall_type: Type[WALL]):
        if not new_cell:
            return
        if start_cell.type is BotCellTypes.CellExit:
            return
        if new_cell.type is BotCellTypes.CellRiver and new_cell.direction is -turn_direction:
            raise UnreachableState()
        if start_cell.type is BotCellTypes.CellRiver and start_cell.direction is turn_direction:
            raise UnreachableState()
        if new_cell.type in [BotCellTypes.NoneCell, BotCellTypes.PossibleExit]:
            wall_type = wall.WallOuter
            self._update_cell_type(BotCellTypes.NoneCell, new_cell.position)
        self.field.add_wall(start_cell.position, turn_direction, wall_type)

    def _calc_possible_river_trajectories(
            self, current_cell: BotCell,  # todo ensure that type is UnknownCell | CellRiver
            type_cell_after_wall_check: BotCellTypes,  # todo CellRiver | CellRiverMouth
            type_cell_turn_end: BotCellTypes,  # todo CellRiver | CellRiverMouth
            is_diff_cells: bool,
            current_player: str,
            turn_direction: Directions | None) -> list['FieldState']:
        # река-река: type_cell_after_wall_check == river, type_cell_turn_end == river, is_diff_cells = True
        # река-устье: type_cell_after_wall_check == river, type_cell_turn_end == mouth, is_diff_cells = True
        # река: type_cell_after_wall_check == river, type_cell_turn_end == river, is_diff_cells = False

        # ... , река, ...
        if type_cell_after_wall_check is BotCellTypes.CellRiver and not is_diff_cells:
            final_states = self._get_possible_leaves(current_cell, current_player, turn_direction)
            if not final_states:
                raise UnreachableState()
            return final_states

        # ... , река-река / река-устье, ...

        # все варианты течения первой клетки
        new_states = self._get_possible_leaves(current_cell, current_player, turn_direction, washed=True)

        if type_cell_turn_end is not BotCellTypes.CellRiverMouth:
            # все варианты течения второй клетки
            new_states2: list[FieldState] = []
            for new_state in new_states:
                riv_dir = new_state.get_player_cell(current_player).direction
                try:
                    new_states2 += new_state._get_possible_leaves(
                        new_state.field.get_neighbour_cell(new_state.get_player_pos(current_player), riv_dir),
                        current_player,
                        riv_dir)
                except UnreachableState:
                    pass
            final_states: list[FieldState] = []
            for new_state in new_states2:
                riv_dir = new_state.get_player_cell(current_player).direction
                try:
                    final_states += new_state._get_possible_leaves(
                        new_state.field.get_neighbour_cell(new_state.get_player_pos(current_player), riv_dir),
                        current_player,
                        riv_dir)
                except UnreachableState:
                    pass
            if not final_states:
                raise UnreachableState()
            return final_states
        else:  # смыло до устья
            final_states: list[FieldState] = []
            new_states2: list[FieldState] = []
            for new_state in new_states:
                riv_dir = new_state.get_player_cell(current_player).direction
                current_cell = new_state.field.get_neighbour_cell(new_state.get_player_pos(current_player), riv_dir)
                if current_cell.type is BotCellTypes.CellRiverMouth:
                    new_state._move_player(current_player, current_cell.position)
                    final_states.append(new_state)
                else:
                    try:
                        new_states2 += new_state._get_possible_leaves(current_cell, current_player, riv_dir)
                    except UnreachableState:
                        pass
                    if current_cell.type is BotCellTypes.UnknownCell:
                        try:
                            final_states.append(
                                new_state._get_modified_copy(current_cell.position, type_cell_turn_end, current_player))
                        except UnreachableState:
                            pass

            for new_state in new_states2:
                riv_dir = new_state.get_player_cell(current_player).direction
                current_cell = new_state.field.get_neighbour_cell(new_state.get_player_pos(current_player), riv_dir)
                if current_cell.type is BotCellTypes.CellRiverMouth:
                    new_state._move_player(current_player, current_cell.position)
                    final_states.append(new_state)
                else:
                    try:
                        final_states.append(
                            new_state._get_modified_copy(current_cell.position, type_cell_turn_end, current_player))
                    except UnreachableState:
                        pass
            if not final_states:
                raise UnreachableState()
            return final_states

    def _get_possible_leaves(self,
                             current_cell: BotCell,  # todo UnknownCell | CellRiver,
                             current_player: str,
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
            if prev_cell.type is BotCellTypes.CellRiver and prev_cell.direction is turn_direction:
                raise UnreachableState()

        possible_river_dirs = self.field.get_possible_river_directions(current_cell, turn_direction, washed)
        if not possible_river_dirs:
            raise UnreachableState()

        if current_cell.type is BotCellTypes.UnknownCell:
            leaves = [self._get_modified_copy(current_cell.position, BotCellTypes.CellRiver, current_player, direction)
                      for direction in possible_river_dirs]
            return leaves
        elif current_cell.type is BotCellTypes.CellRiver and current_cell.direction in possible_river_dirs:
            self._move_player(current_player, current_cell.position)
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
