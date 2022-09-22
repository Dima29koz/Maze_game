import networkx as nx

from GameEngine.globalEnv.enums import Directions
from GameEngine.globalEnv.types import Position
from bots_ai.field_handler.field_obj import NoneCell
from bots_ai.field_handler.grid import Grid, CELL


class GraphBuilder:
    def __init__(self, game_map: Grid):
        self.graph = self.build_from_map(game_map)

    def build_from_map(self, game_map: Grid):
        graph = nx.MultiDiGraph()
        graph.add_nodes_from(game_map.get_cells())
        # for node in graph.nodes:
        #     connected_cells = self.get_connected_cells(node)
        #     for connected_cell, direction in connected_cells:
        #         graph.add_edge(node, connected_cell, direction=direction)

        graph.add_edge(game_map.get_cell(Position(2, 0)), game_map.get_cell(Position(3, 2)), direction='bot')
        graph.add_edge(game_map.get_cell(Position(3, 2)), game_map.get_cell(Position(3, 3)), direction='bot')
        # graph.add_edge(game_map.get_cell(Position(2, 0)), game_map.get_cell(Position(2, 0)), direction='top')
        # graph.add_edge(game_map.get_cell(Position(2, 0)), game_map.get_cell(Position(2, 0)), direction='right')
        # graph.add_edge(game_map.get_cell(Position(2, 0)), game_map.get_cell(Position(2, 0)), direction='left')
        #
        # graph.add_edge(game_map.get_cell(Position(2, 1)), game_map.get_cell(Position(3, 1)), direction='left')
        # graph.add_edge(game_map.get_cell(Position(3, 1)), game_map.get_cell(Position(2, 0)), direction='left')

        return graph

    def get_path(self, graph, source, target):
        path = nx.shortest_path(graph, source, target)
        # path = nx.shortest_path(graph, game_map.get_cell(Position(3, 3)), game_map.get_cell(Position(2, 0)))
        print('path to node\n', path)
        path_graph = nx.path_graph(path)

        print('detailed path to target node')
        # Read attributes from each edge
        for edge in path_graph.edges():
            print(edge, graph.get_edge_data(edge[0], edge[1]))
            # print(edge, graph.edges[edge[0], edge[1]])

    def get_connected_cells(self, cell: CELL) -> list[tuple[CELL, Directions]]:
        if type(cell) is NoneCell:
            return []




