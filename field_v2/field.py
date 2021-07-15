from cell import *
import random

class Field:
    def __init__(self, n, m):
        self.grid = [[None] * m for i in range(n)]
        for i in range(0, n):
            for j in range(0, m):
                self.grid[i][j] = Cell(self.grid[i+1][j] if i+1 in range(0,n) and self.grid[i+1][j] else None,
                                       self.grid[i-1][j] if i-1 in range(0,n) and self.grid[i-1][j] else None,
                                       self.grid[i][j-1] if j-1 in range(0,m) and self.grid[i][j-1] else None,
                                       self.grid[i][j+1] if j+1 in range(0,m) and self.grid[i][j+1] else None)
        self.gen_river(5)

    def gen_river_source(self):
        a = random.randint(0, len(self.grid) - 1)
        b = random.randint(0, len(self.grid[0]) - 1)
        return a,b

    def gen_river(self, length):
        river = []
        tmpgrid = [[True] * len(self.grid[0]) for i in range(len(self.grid))]
        while any(any(x) for x in tmpgrid):
            x, y = self.gen_river_source()
            tmpgrid[x][y] = False
            if isinstance(self.grid[x][y], Cell):
                self.grid[x][y] = CellRiver(self.grid[x][y].right_cell, self.grid[x][y].left_cell, self.grid[x][y].top_cell, self.grid[x][y].bottom_cell, river)
                river.append(self.grid[x][y])
                river = self.gen_next_river_cell(length - 1, river)
            if len(river):
                pass

    def gen_next_river_cell(self, length, river):
        pass
