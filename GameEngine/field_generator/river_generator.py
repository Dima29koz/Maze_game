from random import choice, shuffle

from GameEngine.field_generator.level_pattern import PatternCell
from GameEngine.globalEnv.enums import Directions
from GameEngine.field.cell import Cell, CellRiver, CellRiverMouth


class RiverGenerator:
    def __init__(self, cols, rows,
                 pattern: list[list[PatternCell]],
                 field: list[list[Cell]],
                 ground_cells: list[Cell]):
        self.__cols, self.__rows = cols, rows
        self.__pattern = pattern
        self.__field = field
        self.__ground_cells = ground_cells

    def spawn_rivers(self, river_lengths) -> list[list[CellRiver]]:
        rivers = []
        for length in river_lengths:
            river = self.generate_river(length)
            if river:
                rivers.append(river)
        return rivers

    def generate_river(self, length) -> list[CellRiver] | None:
        river_tmp = self.__gen_river(length)
        if not river_tmp:
            return
        river = [CellRiver(riv_cell.x, riv_cell.y) for riv_cell in river_tmp]
        river[-1] = CellRiverMouth(river[-1].x, river[-1].y)
        for riv_cell in river:
            riv_cell.add_river_list(river)
            self.__field[riv_cell.y][riv_cell.x] = riv_cell
        return river

    def __gen_river(self, length) -> list[Cell] | None:
        shuffle(self.__ground_cells)
        for source in self.__ground_cells:
            river = self.__gen_next_river_cell(length - 1, [source])
            if river:
                for cell in river:
                    self.__ground_cells.remove(cell)
                return river

    def __check_directions(self, current_cell: Cell) -> list[Cell] | None:
        empty_neighbours = []
        for direction in Directions:
            x, y = direction.calc(current_cell.x, current_cell.y)
            if x in range(self.__cols) and y in range(self.__rows) and \
                    not self.__pattern[y][x].visited and type(self.__field[y][x]) == Cell:
                empty_neighbours.append(self.__field[y][x])
        return empty_neighbours

    def __gen_next_river_cell(self, length, river: list[Cell]) -> list[Cell] | None:
        if length == 0:
            self.__pattern[river[-1].y][river[-1].x].visited = True
            return river
        else:
            empty_neighbours = self.__check_directions(river[-1])

            while empty_neighbours:
                next_cell = choice(empty_neighbours)
                empty_neighbours.remove(next_cell)
                self.__pattern[river[-1].y][river[-1].x].visited = True
                river.append(next_cell)
                a = self.__gen_next_river_cell(length - 1, river)
                if a:
                    return a
            else:
                last = river.pop()
                self.__pattern[last.y][last.x].visited = False
                return
