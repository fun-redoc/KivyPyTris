from typing import *
from Shape import *
from definitions import *
import random


def grid_pos(x, y):
    assert not to_grid_pos(x, y) is None
    return x + (y * GRID_WIDTH)


def to_grid_pos(x: int, y: int) -> Optional[int]:
    if not 0 <= x < GRID_WIDTH:
        return None
    if not 0 <= y < GRID_HEIGHT:
        return None
    return x + (y * GRID_WIDTH)


def shape_to_grid(shape: Shape) -> List[Tuple[int, int]]:
    coords = []
    templ = shapes[shape.shapeIdx]
    templ_rotated = templ[shape.rotation % len(templ)]
    for (y, row) in enumerate(templ_rotated):
        for (x, cell) in enumerate(row):
            if cell == 'X':
                coords.append((shape.x + x + SHAPE_OFFSET_X, shape.y + y + SHAPE_OFFSET_Y))
    return coords


def is_spawn_pos(acoord: Tuple[int, int]) -> bool:
    return acoord[1] < 0


def is_within_grid(x: int, y: int) -> bool:
    return 0 <= x < GRID_WIDTH and y < GRID_HEIGHT


def space_valid_for_shape(shape: Shape, occupied_positions: Dict[Tuple[int, int], Shape]) -> bool:
    shape_coords = shape_to_grid(shape)
    for (x, y) in shape_coords:
        if (x, y) in occupied_positions:
            return False
        if not is_within_grid(x, y):
            return False
    return True


def check_lost(positions: Dict[Tuple[int, int], Shape]) -> bool:
    """
    check if any position is above the screen
    """
    for (_, y) in positions.keys():
        if 0 > y:
            return True
    return False


def new_shape():
    return Shape(SHAPE_START_X, SHAPE_START_Y, random.choice(shapes))
