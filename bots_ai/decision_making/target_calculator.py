from bots_ai.field_handler.graph_builder import GraphBuilder
from bots_ai.field_handler.grid import CELL, cell, UnknownCell, PossibleExit


class TargetCalculator:
    def __init__(self, graph: GraphBuilder):
        self.graph = graph

    def get_target(self) -> CELL:
        res = []
        cell_wight = {
            UnknownCell: 10,
            PossibleExit: 8,
        }
        for target, path_len in self.graph.paths_len.items():
            try:
                wight = cell_wight.get(type(target), 1) / path_len
                res.append((target, wight))
            except ZeroDivisionError:
                pass
        res = sorted(res, key=lambda item: -item[1])
        # print(res)
        return res[0][0]
