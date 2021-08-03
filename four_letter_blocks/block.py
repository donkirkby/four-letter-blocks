import typing
from collections import defaultdict
from copy import copy

from PySide6.QtGui import QPainter

from four_letter_blocks.grid import Grid
from four_letter_blocks.square import Square


class Block:
    def __init__(self, *squares: Square):
        self.squares = squares

    def __repr__(self):
        squares = ', '.join(repr(square) for square in self.squares)
        return f"Block({squares})"

    @staticmethod
    def parse(text: str, grid: Grid) -> typing.List['Block']:
        square_lists = defaultdict(list)
        lines = text.splitlines()
        for y, line in enumerate(lines):
            for x, letter in enumerate(line):
                if letter == '#':
                    continue
                square = copy(grid[x, y])
                square.x = x
                square.y = y
                square_list = square_lists[letter]
                square_list.append(square)
        blocks = [Block(*square_list) for square_list in square_lists.values()]
        return blocks

    @property
    def x(self):
        return min(square.x for square in self.squares)

    @x.setter
    def x(self, value):
        dx = value - self.x
        for square in self.squares:
            square.x += dx

    @property
    def y(self):
        return min(square.y for square in self.squares)

    @y.setter
    def y(self, value):
        dy = value - self.y
        for square in self.squares:
            square.y += dy

    @property
    def width(self):
        right = self.squares[0].size + max(square.x for square in self.squares)
        return right - self.x

    @property
    def height(self):
        bottom = self.squares[0].size + max(square.y for square in self.squares)
        return bottom - self.y

    def draw(self, painter: QPainter):
        for square in self.squares:
            square.draw(painter)
