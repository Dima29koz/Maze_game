from typing import Type

from GameEngine.entities.player import Player
from GameEngine.field import cell
from GameEngine.field import wall
from GameEngine.globalEnv.enums import Directions, Actions
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
        self.next_states = []

    def get_current_data(self):
        return self.field, self.player


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

    def get_fields(self):
        """returns all leaves of a tree"""
        leaves = []
        self._collect_leaf_nodes(self.field_root, leaves)
        return leaves

    def process_turn_resp(self, raw_response: dict):
        action = Actions[raw_response.get('action')]
        direction = Directions[raw_response.get('direction')] if raw_response.get('direction') else None
        player_name = raw_response.get('player_name')
        response = raw_response.get('response')
        type_cell_turn_end = response.get('type_cell_at_end_of_turn', None)

        if action == Actions.info:
            pos_x = self.field_root.player.cell.x
            pos_y = self.field_root.player.cell.y
            self._update_cell_type(type_cell_turn_end, pos_x, pos_y)
        if action == Actions.move:
            x, y = direction.calc(self.field_root.player.cell.x, self.field_root.player.cell.y)
            self.field_root.player.move(self.field_root.field[y][x])
            pos_x = self.field_root.player.cell.x
            pos_y = self.field_root.player.cell.y
            self._update_cell_type(type_cell_turn_end, pos_x, pos_y)

    def _calc_possible_trajectories(self):
        pass

    def _update_cell_type(self, new_type: Type[cell.Cell], pos_x: int, pos_y: int):
        if new_type is cell.CellExit:
            print('exit')  # fixme
            return
        neighbours = self.field_root.field[pos_y][pos_x].neighbours
        walls = self.field_root.field[pos_y][pos_x].walls
        self.field_root.field[pos_y][pos_x] = new_type(pos_x, pos_y)
        self.field_root.field[pos_y][pos_x].change_neighbours(neighbours)
        self.field_root.field[pos_y][pos_x].walls = walls

    def _collect_leaf_nodes(self, node, leaves):
        if node is not None:
            if not node.next_states:
                leaves.append(node.get_current_data())
            for n in node.next_states:
                self._collect_leaf_nodes(n, leaves)

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
