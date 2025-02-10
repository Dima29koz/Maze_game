from .field_handler.common_data import CommonData
from .field_handler.field_obj import BotCell, BotCellTypes, UnbreakableWall
from .field_handler.field_state import FieldState
from .field_handler.grid import Grid
from .field_handler.tree_node import Node
from ..game_engine.field import wall
from ..game_engine.global_env.enums import Directions
from ..game_engine.global_env.types import Position
from ..game_engine.rules import get_rules


class InitGenerator:
    def __init__(self, game_rules: dict, players: dict[str, Position]):
        self._rules = game_rules
        self._players = players
        self._size_x: int = game_rules.get('generator_rules').get('cols')
        self._size_y: int = game_rules.get('generator_rules').get('rows')
        self._cols = self._size_x + 2
        self._rows = self._size_y + 2
        self._unique_objs = self._gen_field_objs_amount()
        self._spawn_points = self._gen_spawn_points()
        self.common_data = CommonData(game_rules)

    def get_start_state(self, player_name: str) -> Node:
        other_players = [pl_name for pl_name in self._players.keys() if pl_name != player_name]
        base_grid = self._generate_base_grid()
        base_state = FieldState(
            base_grid,
            self.get_unique_obj_amount(),
            {player_name: None for player_name in self._players},
            self.common_data,
            treasures_positions=[],
        )
        root_state = Node(
            base_state,
            {player_name: True for player_name in other_players},
            {player_name: None for player_name in other_players}
        )
        for position in self._spawn_points:
            next_state = root_state.copy(player_position=(player_name, position))
            if position == self._players.get(player_name):
                next_state.is_real_spawn = True
            root_state.next_states.append(next_state)
        return root_state

    def get_unique_obj_amount(self) -> dict[BotCellTypes, int]:
        return self._unique_objs.copy()

    def _gen_field_objs_amount(self) -> dict[BotCellTypes, int]:
        obj_amount = {
            BotCellTypes.CellClinic: 1,
        }
        if self._rules.get('generator_rules').get('is_separated_armory'):
            obj_amount.update({
                BotCellTypes.CellArmoryWeapon: 1,
                BotCellTypes.CellArmoryExplosive: 1,
            })
        else:
            obj_amount.update({
                BotCellTypes.CellArmory: 1,
            })
        return obj_amount

    def _gen_spawn_points(self):
        xr = range(1, self._size_x + 1)
        yr = range(1, self._size_y + 1)
        return [Position(x, y) for y in yr for x in xr]

    def _generate_base_grid(self) -> Grid:
        none_cols = [0, self._cols - 1]
        none_rows = [0, self._rows - 1]

        field = [[BotCell(
            Position(col, row),
            BotCellTypes.UnknownCell
            if row not in none_rows and col not in none_cols
            else BotCellTypes.NoneCell
        )
            for col in range(self._cols)] for row in range(self._rows)]
        # self._create_border_walls(field)
        self._create_possible_exits(field)
        return Grid(field)

    @staticmethod
    def _create_possible_exits(field: list[list[BotCell]]):
        for row in field:
            for cell_obj in row:
                if cell_obj.type is BotCellTypes.NoneCell:
                    for direction in Directions:
                        x, y = direction.get_neighbour_cords(cell_obj.position.x, cell_obj.position.y)
                        try:
                            neighbour = field[y][x]
                        except IndexError:
                            neighbour = None
                        if neighbour and neighbour.type not in [BotCellTypes.NoneCell, BotCellTypes.PossibleExit]:
                            field[cell_obj.position.y][cell_obj.position.x] = BotCell(
                                cell_obj.position, BotCellTypes.PossibleExit, direction)
                            neighbour.add_wall(-direction, wall.WallExit())

    @staticmethod
    def _create_border_walls(field: list[list[BotCell]]):
        for row in field:
            for cell_obj in row:
                if cell_obj.type is BotCellTypes.NoneCell:
                    for direction in Directions:
                        x, y = direction.get_neighbour_cords(cell_obj.position.x, cell_obj.position.y)
                        try:
                            neighbour = field[y][x]
                        except IndexError:
                            neighbour = None
                        if neighbour and neighbour.type is not BotCellTypes.NoneCell:
                            neighbour.add_wall(-direction, UnbreakableWall())


def make_example_grid():
    init_gen = InitGenerator(get_rules(), {'p1': Position(1, 1)})
    grid = init_gen.get_start_state('p1').field_state.field

    grid.create_exit(Directions.bottom, Position(2, 0))

    pos = Position(2, 1)
    walls = grid.get_cell(pos).walls
    grid.set_cell(BotCell(pos, BotCellTypes.CellRiver, Directions.right), pos)
    grid.set_walls(pos, walls)
    grid.add_wall(pos, Directions.right, wall.WallEmpty)

    pos = Position(3, 1)
    walls = grid.get_cell(pos).walls
    grid.set_cell(BotCell(pos, BotCellTypes.CellRiver, Directions.bottom), pos)
    grid.set_walls(pos, walls)
    grid.add_wall(pos, Directions.bottom, wall.WallEmpty)

    pos = Position(3, 2)
    walls = grid.get_cell(pos).walls
    grid.set_cell(BotCell(pos, BotCellTypes.CellRiverMouth), pos)
    grid.set_walls(pos, walls)

    pos = Position(3, 3)
    walls = grid.get_cell(pos).walls
    grid.set_cell(BotCell(pos, BotCellTypes.Cell), pos)
    grid.set_walls(pos, walls)
    return grid
