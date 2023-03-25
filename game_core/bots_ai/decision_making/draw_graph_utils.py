import networkx as nx
import matplotlib

from ...game_engine.global_env.types import LevelPosition
from ..field_handler.grid import Grid

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from ...game_engine.rules import rules as ru
from .graph_builder import GraphBuilder
from ...game_engine.game import Game


def test_graph(grid, player_cell=None, player_abilities=None):
    for row in grid.get_field():
        print(row)
    print('\n')
    gb = GraphBuilder(grid, player_cell, player_abilities)
    gr = gb.graph
    print('nodes\n', gr.nodes)
    # print('edges\n', gr.edges(data=True))
    draw(gr)
    return gb


def draw(graph):
    options = {
        'with_labels': True,
        'width': 1,
        'arrowstyle': '-|>',
        'arrowsize': 12,
    }
    pos = {node: (node.position.get()) for node in graph.nodes}
    ax = plt.gca()
    ax.invert_yaxis()
    nx.draw_networkx(graph, pos=pos, arrows=True, **options)

    plt.show()


def get_real_grid():
    rules = ru
    rules['generator_rules']['seed'] = 5
    f = Game(rules).field.game_map.get_level(LevelPosition(0, 0, 0)).field
    return Grid(f)
