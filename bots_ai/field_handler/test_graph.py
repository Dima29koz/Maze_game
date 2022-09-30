import networkx as nx
import numpy as np
import matplotlib

from GameEngine.globalEnv.types import LevelPosition, Position
from bots_ai.field_handler.grid import Grid

matplotlib.use('TkAgg')
import matplotlib.pyplot as plt

from GameEngine.rules import rules as ru
from bots_ai.field_handler.graph_builder import GraphBuilder
from bots_ai.initial_generator import make_example_grid
from GameEngine.game import Game


def test_graph(grid):
    for row in grid.get_field():
        print(row)
    print('\n')
    gb = GraphBuilder(grid, None)
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


def main():
    test_graph(make_example_grid())


if __name__ == "__main__":
    main()
