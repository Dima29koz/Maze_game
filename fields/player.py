from logic import Directions
from cell import *


class Player:
    def __init__(self, cell):
        self.cell = cell
        self.direction = Directions.mouth
        self.health = 2
        self.bombs = 3
        self.arrows = 3

    def move(self, cell):
        self.cell = cell

    def set_direction(self, direction):
        self.direction = direction
