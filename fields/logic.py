import enum


class Directions(enum.Enum):
    mouth = 0
    top = 1
    right = 2
    bottom = 3
    left = 4


def dir_calc(x, y, direction):
    new_x = x
    new_y = y
    if direction == Directions.top:
        new_y = y - 1
    if direction == Directions.bottom:
        new_y = y + 1
    if direction == Directions.right:
        new_x = x + 1
    if direction == Directions.left:
        new_x = x - 1
    print(f'dir_calc: ({x},{y}),({new_x},{new_y})')
    return new_x, new_y


def is_same_river(cell, new_cell, direction):
    if cell.direction == direction:
        return True
    if new_cell.direction == Directions.top and direction == Directions.bottom:
        return True
    if new_cell.direction == Directions.bottom and direction == Directions.top:
        return True
    if new_cell.direction == Directions.left and direction == Directions.right:
        return True
    if new_cell.direction == Directions.right and direction == Directions.left:
        return True
    return False
