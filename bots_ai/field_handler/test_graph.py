from bots_ai.field_handler.graph_builder import GraphBuilder
from bots_ai.initial_generator import make_example_grid

if __name__ == "__main__":
    f = make_example_grid()
    for row in f.get_field():
        print(row)
    print('\n')
    gb = GraphBuilder(f)
    gr = gb.graph
    print('nodes\n', gr.nodes)
    print('edges\n', gr.edges)
    pass