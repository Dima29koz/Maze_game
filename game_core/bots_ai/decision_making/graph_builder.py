import networkx as nx

from ..field_handler.field_obj import BotCell, BotCellTypes
from ..field_handler.grid import Grid
from ...game_engine.global_env.enums import Directions, Actions


class GraphBuilder:
    def __init__(self, game_map: Grid, current_player_cell: BotCell, player_abilities: dict[Actions, bool]):
        self.game_map = game_map
        self.current_player_cell = current_player_cell
        self._player_abilities = player_abilities
        self.graph = nx.MultiDiGraph()
        self.build_from_map()
        self.paths = self.calc_paths(self.current_player_cell)
        self.paths_len = self.calc_paths_len(self.current_player_cell)

    def build_from_map(self):
        self.graph.add_nodes_from(self.game_map.get_cells())
        for node in self.graph.nodes:
            self._add_related_cells(node)
        return self.graph

    def get_path(self, source: BotCell, target: BotCell):
        path = nx.shortest_path(self.graph, source, target, weight='weight')
        print('path to node\n', path)

        print('detailed path to target node')
        for i, node in enumerate(path[:-1]):
            print(node, self.graph.get_edge_data(node, path[i + 1]))

    def calc_paths(self, source: BotCell) -> dict[BotCell, list[BotCell]]:
        return nx.shortest_path(self.graph, source, weight='weight')

    def calc_paths_len(self, source: BotCell) -> dict[BotCell, int]:
        return nx.shortest_path_length(self.graph, source, weight='weight')

    def get_first_act(self, target: BotCell) -> tuple[Actions, Directions | None]:
        edge_data = self.graph.get_edge_data(self.current_player_cell, self.paths[target][1])
        # print(target.position.get(), edge_data)
        args: dict = list(edge_data.values())[0]
        return args.get('action'), args.get('direction')

    def _add_related_cells(self, tile: BotCell):
        if tile.type is BotCellTypes.NoneCell:
            return
        for direction in Directions:
            self._calc_relation_wall_collision(tile, direction)
            if self._player_abilities.get(Actions.throw_bomb):
                self._calc_relation_no_wall_collision(tile, direction)

    def _calc_relation_wall_collision(self, tile: BotCell, direction: Directions):
        if tile.walls[direction].player_collision:
            new_cell = tile
        else:
            new_cell = self.game_map.get_neighbour_cell(tile.position, direction)

        if new_cell.type is BotCellTypes.CellRiver:
            if self.game_map.is_washed(new_cell, tile, direction):
                for _ in range(2):
                    new_cell = self.game_map.get_neighbour_cell(new_cell.position, new_cell.direction)
                    if new_cell.type is not BotCellTypes.CellRiver:
                        break

        self.graph.add_edge(tile, new_cell, direction=direction, action=Actions.move, weight=1)

    def _calc_relation_no_wall_collision(self, tile: BotCell, direction: Directions):
        if not tile.walls[direction].player_collision:
            return
        if not tile.walls[direction].breakable:
            return

        new_cell = self.game_map.get_neighbour_cell(tile.position, direction)

        if not new_cell:
            return

        if new_cell.type is BotCellTypes.CellRiver:
            if self.game_map.is_washed(new_cell, tile, direction):
                for _ in range(2):
                    new_cell = self.game_map.get_neighbour_cell(new_cell.position, new_cell.direction)
                    if new_cell.type is not BotCellTypes.CellRiver:
                        break

        self.graph.add_edge(tile, new_cell, direction=direction, action=Actions.throw_bomb,
                            weight=1 + (1 if tile.type is not BotCellTypes.CellRiver else 2))
