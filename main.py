from field_generator.field_generator import FieldGenerator

# f = FieldGenerator(5, 4)
# for i in range(4):
#     for j in range(5):
#         print(f.field[i][j].x, f.field[i][j].y)
# f.print()

# print(f.field[0][3].neighbours)

from enum import Enum, auto


class Directions(Enum):
    mouth = 0
    top = 1
    right = 2
    bottom = 3
    left = 4

    def __neg__(self):
        if self is Directions.top:
            return Directions.bottom
        if self is Directions.bottom:
            return Directions.top
        if self is Directions.left:
            return Directions.right
        if self is Directions.right:
            return Directions.left
        if self is Directions.mouth:
            return Directions.mouth

    def calc(self, x, y):
        if self is Directions.top:
            y -= 1
        elif self is Directions.bottom:
            y += 1
        elif self is Directions.left:
            x -= 1
        elif self is Directions.right:
            x += 1
        return x, y

