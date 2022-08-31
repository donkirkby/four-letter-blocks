import math
import typing
from collections import defaultdict
from copy import copy
from functools import cache
from operator import attrgetter
from textwrap import dedent

from PySide6.QtGui import QPainter, QPen, Qt

from four_letter_blocks.grid import Grid
from four_letter_blocks.square import Square


class Block:
    UNUSED = 'unused'
    CUT_COLOUR = '#ed2224'  # Special colour for Game Crafter cutting

    def __init__(self, *squares: Square, marker: str = None):
        self.squares = squares
        self.marker = marker
        self.border_colour = 'black'
        self.divider_colour = 'black'
        coordinates = normalize_coordinates(
            [(square.x, square.y) for square in squares])
        self.shape, self.shape_rotation = shape_rotations().get(coordinates,
                                                                (None, 0))
        self.display_x: typing.Optional[int] = None
        self.display_y: typing.Optional[int] = None
        self.display_rotation: typing.Optional[int] = None

    def __repr__(self):
        squares = ', '.join(repr(square) for square in self.squares)
        return f"Block({squares})"

    @property
    def face_colour(self):
        return self.squares[0].face_colour

    @face_colour.setter
    def face_colour(self, colour):
        for square in self.squares:
            square.face_colour = colour

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
        self.transform_painter(painter, 1)
        square_positions = self.square_positions
        size = self.squares[0].size
        old_pen = painter.pen()
        divider_pen = QPen(self.divider_colour)
        divider_pen.setWidth(old_pen.width())
        for square in self.squares:
            square.draw(painter, use_text=use_text)
            x = square.x
            y = square.y
            painter.setPen(divider_pen)
            if (round(x), round(y-size)) in square_positions:
                painter.drawLine(x, y, x+size, y)
            if (round(x-size), round(y)) in square_positions:
                painter.drawLine(x, y, x, y+size)
            painter.setPen(old_pen)
        self.transform_painter(painter, -1)

        self.draw_outline(painter)

    def draw_outline(self, painter, nick_radius=0):
        self.transform_painter(painter, 1)
        square_positions = self.square_positions
        size = self.squares[0].size
        old_pen = painter.pen()
        outer_pen = QPen(self.border_colour)
        outer_pen.setWidth(math.floor(size / 33))
        if nick_radius:
            outer_pen.setCapStyle(Qt.FlatCap)
        else:
            outer_pen.setCapStyle(Qt.RoundCap)
        for square in self.squares:
            painter.setPen(outer_pen)
            x = square.x
            y = square.y
            if (round(x), round(y - size)) not in square_positions:
                self.draw_nicked_line(painter, nick_radius, x, y, x + size, y)
            if (round(x), round(y + size)) not in square_positions:
                self.draw_nicked_line(painter,
                                      nick_radius,
                                      x, y + size,
                                      x + size, y + size)
            if (round(x - size), round(y)) not in square_positions:
                self.draw_nicked_line(painter, nick_radius, x, y, x, y + size)
            if (round(x + size), round(y)) not in square_positions:
                self.draw_nicked_line(painter,
                                      nick_radius,
                                      x + size, y,
                                      x + size, y + size)
            painter.setPen(old_pen)
        self.transform_painter(painter, -1)

    def draw_nicked_line(self,
                         painter: QPainter,
                         nick_radius: int,
                         x1: int,
                         y1: int,
                         x2: int,
                         y2: int):
        if nick_radius == 0:
            painter.drawLine(x1, y1, x2, y2)
            return

        square_size = self.squares[0].size
        length = max(abs(x2-x1), abs(y2-y1))
        cell_count = round(length / square_size)
        xstep = (x2-x1) / (cell_count*2)
        ystep = (y2-y1) / (cell_count*2)
        xnick = ynick = 0
        if xstep > 0:
            xnick = nick_radius
        elif xstep < 0:
            xnick = -nick_radius
        elif ystep > 0:
            ynick = nick_radius
        else:
            ynick = -nick_radius
        painter.drawLine(x1, y1, round(x1+xstep-xnick), round(y1+ystep-ynick))
        for i in range(cell_count-1):
            painter.drawLine(round(x1+xstep*(2*i+1)+xnick),
                             round(y1+ystep*(2*i+1)+ynick),
                             round(x1+xstep*(2*i+3)-xnick),
                             round(y1+ystep*(2*i+3)-ynick))
        painter.drawLine(round(x2-xstep+xnick), round(y2-ystep+ynick), x2, y2)

    @property
    def square_positions(self):
        return {(round(square.x), round(square.y))
                for square in self.squares}

    def transform_painter(self, painter, sign):
        x_change = y_change = rotation_change = 0
        if self.display_x is not None:
            rotation_change = ((self.shape_rotation + 4 -
                                self.display_rotation) % 4) * 90
            if rotation_change == 0:
                x_change = self.display_x - self.x
                y_change = self.display_y - self.y
            elif rotation_change == 90:
                x_change = self.display_x + self.height + self.y
                y_change = self.display_y - self.x
            elif rotation_change == 180:
                x_change = self.display_x + self.width + self.x
                y_change = self.display_y + self.height + self.y
            else:
                x_change = self.display_x - self.y
                y_change = self.display_y + self.width + self.x
        if sign > 0:
            painter.translate(sign * x_change, sign * y_change)
            painter.rotate(sign * rotation_change)
        else:
            painter.rotate(sign * rotation_change)
            painter.translate(sign * x_change, sign * y_change)

    def set_display(self, x: int, y: int, rotation: int):
        self.display_x = x
        self.display_y = y
        self.display_rotation = rotation

    def calculate_coordinates(self):
        return {(square.x, square.y) for square in self.squares}


@cache
def shape_rotations() -> typing.Dict[
        typing.FrozenSet[typing.Tuple[int, int]],
        typing.Tuple[str, int]]:
    """ A lookup table from a set of (x, y) pairs to name and rotation. """
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
