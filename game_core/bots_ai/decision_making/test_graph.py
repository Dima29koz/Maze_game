from game_core.bots_ai.decision_making.draw_graph_utils import test_graph
from game_core.bots_ai.initial_generator import make_example_grid


def main():
    test_graph(make_example_grid())


if __name__ == "__main__":
    main()