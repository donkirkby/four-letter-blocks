import typing
from collections import defaultdict
from copy import copy
from functools import cache
from operator import attrgetter
from textwrap import dedent

from PySide6.QtGui import QPainter

from four_letter_blocks.grid import Grid
from four_letter_blocks.square import Square


class Block:
    UNUSED = 'unused'

    def __init__(self, *squares: Square, marker: str = None):
        self.squares = squares
        self.marker = marker
        coordinates = normalize_coordinates(
            [(square.x, square.y) for square in squares])
        self.shape, self.shape_rotation = shape_rotations().get(coordinates,
                                                                (None, 0))

    def __repr__(self):
        squares = ', '.join(repr(square) for square in self.squares)
        return f"Block({squares})"

    @staticmethod
    def parse(text: str, grid: Grid) -> typing.List['Block']:
        unused_squares = {square
                          for row in grid.squares
                          for square in row
                          if square is not None}
        square_lists = defaultdict(list)
        lines = text.splitlines()
        for y, line in enumerate(lines):
            for x, marker in enumerate(line):
                if marker in '#?':
                    continue
                try:
                    old_square = grid[x, y]
                except IndexError:
                    continue
                if old_square is None:
                    continue
                unused_squares.remove(old_square)
                square = copy(old_square)
                square.x = x
                square.y = y
                square_list = square_lists[marker]
                square_list.append(square)
        if unused_squares:
            square_list = list(unused_squares)
            square_list.sort(key=attrgetter('y', 'x'))
            square_lists[Block.UNUSED] = square_list
        blocks = [Block(*square_list, marker=marker)
                  for marker, square_list in sorted(square_lists.items())]
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

    def draw(self, painter: QPainter, use_text=True):
        for square in self.squares:
            square.draw(painter, use_text=use_text)


@cache
def shape_rotations() -> typing.Dict[
        typing.FrozenSet[typing.Tuple[int, int]],
        typing.Tuple[str, int]]:
    """ Generate a lookup table from a set of squares to name and rotation. """
    shapes_text = dedent("""\
        OO
        OO
        
        I
        I
        I
        I
        
        L
        L
        LL
        
         J
         J
        JJ
        
         SS
        SS
        
        ZZ
         ZZ
        
        TTT
         T
        """)
    sections = shapes_text.split('\n\n')
    names = {}
    for section in sections:
        name = section.replace(' ', '')[0]
        lines = section.splitlines()
        section_coordinates = []
        for y, line in enumerate(lines):
            for x, letter in enumerate(line):
                if letter != ' ':
                    section_coordinates.append((x, y))
        for rotation in range(4):
            names.setdefault(normalize_coordinates(section_coordinates),
                             (name, rotation))
            section_coordinates = [(y, -x) for x, y in section_coordinates]
    return names


def normalize_coordinates(coordinates: typing.Sequence[
        typing.Tuple[int, int]]) -> typing.FrozenSet[typing.Tuple[int, int]]:
    min_x = min(pair[0] for pair in coordinates)
    min_y = min(pair[1] for pair in coordinates)
    return frozenset((x - min_x, y - min_y) for x, y in coordinates)
