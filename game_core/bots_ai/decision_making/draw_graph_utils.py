import matplotlib
import networkx as nx

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from ..field_converter import convert_field_from_engine
from ..field_handler.field_obj import BotCell
from ..field_handler.grid import Grid
from ... import Actions
from ...game_engine.global_env.types import LevelPosition
from ...game_engine.rules import get_rules
from .graph_builder import GraphBuilder
from ...game_engine.game import Game


def test_graph(grid: Grid, player_cell: BotCell = None, player_abilities: dict[Actions, bool] = None):
    for row in grid.get_field():
        print(row)
    print('\n')
    gb = GraphBuilder(grid, player_cell, player_abilities or dict())
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
    rules = get_rules()
    rules['generator_rules']['seed'] = 5
    f = Game(rules).field.game_map.get_level(LevelPosition(0, 0, 0)).field
    return Grid(convert_field_from_engine(f))
