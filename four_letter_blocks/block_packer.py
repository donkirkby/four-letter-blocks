import typing
from collections import defaultdict
from functools import cache

import numpy as np
from PySide6.QtGui import QPainter, QPen, Qt

from four_letter_blocks.block import shape_rotations, normalize_coordinates


class BlockPacker:
    def __init__(self, width=0, height=0, tries=-1, start_text: str = None):
        if start_text is None:
            self.width = width
            self.height = height
            self.state = np.zeros((height, width), np.int8)
        else:
            lines = start_text.splitlines()
            self.height = len(lines)
            self.width = self.height and len(lines[0])
            self.state = np.ndarray((self.height, self.width), np.int8)
            for row, line in enumerate(lines):
                for col, char in enumerate(line):
                    self.state[row, col] = (0 if char == '.'
                                            else 1 if char == '#'
                                            else ord(char) - 63)
        self.tries = tries
        self.cell_size = 940
        self.margin = 120
        self.nick_radius = 5

    @property
    def positions(self):
        result = defaultdict(list)
        shape_map = shape_rotations()
        max_block = np.max(self.state)
        for block in range(2, max_block+1):
            # convert row, col to x, y
            y_coordinates, x_coordinates = np.nonzero(self.state == block)
            coordinates = list(zip(x_coordinates, y_coordinates))
            norm_coordinates = normalize_coordinates(coordinates)  # type: ignore
            shape_name, rotation = shape_map[norm_coordinates]
            result[shape_name].append((min(x_coordinates),
                                       min(y_coordinates),
                                       rotation))
        return result

    def display(self, state: np.ndarray = None) -> str:
        if state is None:
            state = self.state
        return '\n'.join(''.join(chr(63+c) if c > 1 else c and '#' or '.'
                                 for c in row)
                         for row in state)

    def fill(self, shape_counts: typing.Counter[str]):
        """ Fill in the current state with the given shapes.

        Cycles through the available shapes in shape_counts, and tries them in
        different positions, looking for the fewest rows. Set the current state
        to a filled in copy, not changing the original.

        :param shape_counts: number of blocks of each shape
        """
        if self.tries == 0:
            self.state = None
            return
        if self.tries > 0:
            self.tries -= 1
        blocks = shape_coordinates()
        best_state = None
        start_state = self.state
        empty = np.nonzero(self.state == 0)
        target_row = empty[0][0]
        target_col = empty[1][0]
        next_block = np.amax(start_state) + 1
        if next_block == 1:
            next_block = 2  # Skip blank value

        fewest_rows = start_state.shape[0]+1
        for shape_name, _ in shape_counts.most_common():
            old_count = shape_counts[shape_name]
            if old_count == 0:
                continue
            shape_counts[shape_name] = old_count - 1
            for block in blocks[shape_name]:
                new_state = start_state.copy()
                target = new_state[
                    target_row:target_row+block.shape[0],
                    target_col:target_col+block.shape[1]
                ]
                if target.shape != block.shape:
                    # hanging over the edge
                    continue
                collisions = np.logical_and(block, target)
                if collisions.any():
                    continue
                target += next_block*block
                self.state = new_state
                if sum(shape_counts.values()):
                    self.fill(shape_counts)
                    if self.state is None:
                        continue
                filled = np.nonzero(self.state != 0)
                if not filled[0].size:
                    used_rows = 0
                else:
                    used_rows = filled[0][-1] + 1
                if used_rows < fewest_rows:
                    best_state = self.state
                    fewest_rows = used_rows
            shape_counts[shape_name] = old_count
        if best_state is not None:
            self.state = best_state
        else:
            start_state[target_row, target_col] = 1  # gap
            self.state = start_state
            self.fill(shape_counts)

    @staticmethod
    def draw_front(painter: QPainter):
        device = painter.device()
        painter.fillRect(0, 0, device.width(), device.height(), 'black')

    @staticmethod
    def draw_back(painter: QPainter):
        device = painter.device()
        painter.fillRect(0, 0, device.width(), device.height(), 'white')

    def draw_cuts(self, painter: QPainter):
        cell_size = self.cell_size
        margin = self.margin
        nick_radius = self.nick_radius

        pen = QPen('#ed2224')
        pen.setWidth(cell_size/20)
        pen.setCapStyle(Qt.FlatCap)

        painter.setPen(pen)
        # L
        painter.drawLine(margin, margin,
                         margin + cell_size*3-nick_radius, margin)
        painter.drawLine(margin + cell_size*3, margin+nick_radius,
                         margin + cell_size*3, margin+cell_size-nick_radius)
        painter.drawLine(margin + cell_size*3-nick_radius, margin+cell_size,
                         margin + cell_size, margin+cell_size)
        painter.drawLine(margin + cell_size, margin+cell_size,
                         margin + cell_size, margin+cell_size*2-nick_radius)
        painter.drawLine(margin + cell_size-nick_radius, margin+cell_size*2,
                         margin + nick_radius, margin+cell_size*2)
        painter.drawLine(margin, margin,
                         margin, margin+cell_size*2-nick_radius)

        # J
        painter.drawLine(margin, margin+cell_size*2+nick_radius,
                         margin, margin+cell_size*4)
        painter.drawLine(margin, margin+cell_size*4,
                         margin+cell_size*3-nick_radius, margin+cell_size*4)
        painter.drawLine(margin+cell_size*3, margin+cell_size*4-nick_radius,
                         margin+cell_size*3, margin+cell_size*3+nick_radius)
        painter.drawLine(margin+cell_size*3-nick_radius, margin+cell_size*3,
                         margin+cell_size, margin+cell_size*3)
        painter.drawLine(margin+cell_size, margin+cell_size*3,
                         margin+cell_size, margin+cell_size*2+nick_radius)

        # O
        painter.drawLine(margin+cell_size*3, margin+cell_size+nick_radius,
                         margin+cell_size*3, margin+cell_size*3-nick_radius)

        # I
        painter.drawLine(margin+cell_size*3+nick_radius, margin,
                         margin+cell_size*4-nick_radius, margin)
        painter.drawLine(margin+cell_size*3+nick_radius, margin+cell_size*4,
                         margin+cell_size*4-nick_radius, margin+cell_size*4)
        painter.drawLine(margin+cell_size*4, margin+nick_radius,
                         margin+cell_size*4, margin+cell_size*3-nick_radius)
        painter.drawLine(margin+cell_size*4, margin+cell_size*3+nick_radius,
                         margin+cell_size*4, margin+cell_size*4-nick_radius)
        painter.drawLine(margin+cell_size*4, margin+cell_size*3+nick_radius,
                         margin+cell_size*4, margin+cell_size*4-nick_radius)

        # T
        painter.drawLine(margin+cell_size*4+nick_radius, margin,
                         margin+cell_size*5-nick_radius, margin)
        painter.drawLine(margin+cell_size*5, margin+nick_radius,
                         margin+cell_size*5, margin+cell_size)
        painter.drawLine(margin+cell_size*5, margin+cell_size,
                         margin+cell_size*6, margin+cell_size)
        painter.drawLine(margin+cell_size*6, margin+cell_size,
                         margin+cell_size*6, margin+cell_size*2-nick_radius)
        painter.drawLine(margin+cell_size*6-nick_radius, margin+cell_size*2,
                         margin+cell_size*5, margin+cell_size*2)
        painter.drawLine(margin+cell_size*5, margin+cell_size*2,
                         margin+cell_size*5, margin+cell_size*3)
        painter.drawLine(margin+cell_size*5, margin+cell_size*3,
                         margin+cell_size*4+nick_radius, margin+cell_size*3)

        # S
        painter.drawLine(margin+cell_size*6, margin+cell_size*4,
                         margin+cell_size*4+nick_radius, margin+cell_size*4)
        painter.drawLine(margin+cell_size*6, margin+cell_size*4,
                         margin+cell_size*6, margin+cell_size*3)
        painter.drawLine(margin+cell_size*6, margin+cell_size*3,
                         margin+cell_size*7, margin+cell_size*3)
        painter.drawLine(margin+cell_size*7, margin+cell_size*3,
                         margin+cell_size*7, margin+cell_size*2+nick_radius)
        painter.drawLine(margin+cell_size*7-nick_radius, margin+cell_size*2,
                         margin+cell_size*6+nick_radius, margin+cell_size*2)

        # Z
        painter.drawLine(margin+cell_size*7+nick_radius, margin+cell_size*2,
                         margin+cell_size*8, margin+cell_size*2)
        painter.drawLine(margin+cell_size*8, margin+cell_size*2,
                         margin+cell_size*8, margin+cell_size)
        painter.drawLine(margin + cell_size*7, margin+cell_size,
                         margin + cell_size*8, margin+cell_size)
        painter.drawLine(margin + cell_size*7, margin+cell_size,
                         margin + cell_size*7, margin)
        painter.drawLine(margin + cell_size*7, margin,
                         margin + cell_size*5+nick_radius, margin)


@cache
def shape_coordinates() -> typing.Dict[str, typing.List[np.ndarray]]:
    coordinate_lists = defaultdict(list)
    for coordinates, (name, rotation) in shape_rotations().items():
        max_x = max(x for x, y in coordinates)
        max_y = max(y for x, y in coordinates)
        grid = np.zeros((max_y+1, max_x+1), np.int8)
        for x, y in coordinates:
            grid[y, x] = 1
        coordinate_lists[name].append(grid)
    return coordinate_lists
