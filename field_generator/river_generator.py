from random import choice
from typing import Optional

from field_generator.level_pattern import PatternCell
from enums import Directions


def gen_river(length, allowed_sources, pattern, cols, rows) -> list[PatternCell]:
    while allowed_sources:
        source = choice(allowed_sources)
        allowed_sources.remove(source)
        river = gen_next_river_cell(length - 1, pattern, [source], cols, rows)
        if river:
            return river


def check_directions(pattern: list[list[PatternCell]], current_cell, cols, rows):
    empty_neighbours = []
    for direction in Directions:
        x, y = direction.calc(current_cell.x, current_cell.y)
        if x in range(0, cols) and y in range(0, rows) and \
                not pattern[y][x].visited and pattern[y][x].is_not_none:
            empty_neighbours.append(pattern[y][x])
    return empty_neighbours


def gen_next_river_cell(length, pattern, river, cols, rows) -> Optional[list[PatternCell]]:
    if length == 0:
        return river
    else:
        empty_neighbours = check_directions(pattern, river[-1], cols, rows)

        while empty_neighbours:
            next_cell = choice(empty_neighbours)
            empty_neighbours.remove(next_cell)
            pattern[river[-1].y][river[-1].x].visited = True
            river.append(next_cell)
            a = gen_next_river_cell(length - 1, pattern, river, cols, rows)
            if a:
                return a
        else:
            last = river.pop()
            pattern[last.y][last.x].visited = False
            return
