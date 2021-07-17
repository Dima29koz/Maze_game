from enums import Actions, Directions
from field.cell import *


class Player:
    def __init__(self, cell):
        self.cell = cell
        self.direction = Directions.mouth
        self.state = Actions.skip
        self.health = 2
        self.bombs = 3
        self.arrows = 3

    def action(self):
        if self.state is Actions.skip:
            self.cell.idle()
        if self.state is Actions.move:
            self.cell.check_wall(self)

