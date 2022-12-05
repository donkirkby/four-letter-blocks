import math
import typing
from collections import defaultdict
from copy import copy
from functools import cache
from operator import attrgetter
from textwrap import dedent

from PySide6.QtCore import QPoint
from PySide6.QtGui import QPainter, QPen, Qt, QPainterPath

from four_letter_blocks.grid import Grid
from four_letter_blocks.square import Square


def create_tab_path(path, square_size):
    curved_portion = 0.75 * square_size
    tab_width = 0.24 * square_size
    stem_width = 0.16 * square_size
    stem_length = 0.25 * square_size
    path.lineTo(-curved_portion / 2, 0)  # E
    path.cubicTo(-curved_portion / 3, 0,  # inner E
                 -1.25 * stem_width, -.5 * stem_length,  # outer D
                 -.781 * stem_width, -.5 * stem_length)  # D
    path.cubicTo(-.5 * stem_width, -.5 * stem_length,  # inner D
                 -.44 * stem_width, -.28 * stem_length,  # outer C
                 -.5 * stem_width, -.2 * stem_length)  # C
    path.cubicTo(-.56 * stem_width, -.12 * stem_length,  # inner C
                 -.5833 * tab_width, .2 * stem_length,  # outer B
                 -tab_width / 2, .28 * stem_length)  # B
    path.cubicTo(-.416667 * tab_width, .36 * stem_length,  # inner B
                 -.416667 * tab_width, 0.5 * stem_length,  # outer A
                 0, 0.5 * stem_length)  # A
    path.cubicTo(.416667 * tab_width, 0.5 * stem_length,  # outer A
                 .416667 * tab_width, .36 * stem_length,  # inner B
                 tab_width / 2, .28 * stem_length)  # B
    path.cubicTo(.5833 * tab_width, .2 * stem_length,  # outer B
                 .56 * stem_width, -.12 * stem_length,  # inner C
                 .5 * stem_width, -.2 * stem_length)  # C
    path.cubicTo(.44 * stem_width, -.28 * stem_length,  # outer C
                 .5 * stem_width, -.5 * stem_length,  # inner D
                 .781 * stem_width, -.5 * stem_length)  # D
    path.cubicTo(1.25 * stem_width, -.5 * stem_length,  # outer D
                 curved_portion / 3, 0,  # inner E
                 curved_portion / 2, 0)  # E
    path.lineTo(square_size / 2, 0)


def create_double_tab_path(path, square_size, nick_radius=0):
    tab_radius = 0.1 * square_size
    shoulder_radius = tab_radius * .6667
    theta = math.asin(1/(1+tab_radius/shoulder_radius))
    theta_deg = theta*180/math.pi

    shoulder_start = -(tab_radius + shoulder_radius) * math.cos(theta)
    path.lineTo(shoulder_start - 2*nick_radius, 0)
    path.moveTo(shoulder_start, 0)
    path.arcTo(-(tab_radius+shoulder_radius)*math.cos(theta)-shoulder_radius,
               -2*shoulder_radius,
               2*shoulder_radius,
               2*shoulder_radius,
               -90,
               90-theta_deg)
    path.arcTo(-tab_radius, -tab_radius,
               2*tab_radius, 2*tab_radius,
               180-theta_deg, -90+theta_deg)
    path.arcTo(-tab_radius/2, -tab_radius, tab_radius, tab_radius, 90, -180)
    path.arcTo(-tab_radius/2, 0, tab_radius, tab_radius, 90, 180)
    path.arcTo(-tab_radius, -tab_radius,
               2*tab_radius, 2*tab_radius,
               270, 90-theta_deg)
    path.arcTo((tab_radius+shoulder_radius)*math.cos(theta)-shoulder_radius, 0,
               2*shoulder_radius, 2*shoulder_radius,
               180-theta_deg, -90+theta_deg)
    path.lineTo(square_size/2, 0)


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
        self.tab_count = 0

    def __repr__(self):
        squares = ', '.join(repr(square) for square in self.squares)
        return f"Block({squares})"

    @staticmethod
    def shape_names() -> typing.List[str]:
        return sorted({name for name, rotation in shape_rotations().values()})

    @property
    def face_colour(self):
        return self.squares[0].face_colour

    @face_colour.setter
    def face_colour(self, colour):
        for square in self.squares:
            square.face_colour = colour

    @staticmethod
    def parse(text: str,
              grid: Grid,
              old_blocks: typing.List[typing.List[str]] = None
              ) -> typing.List['Block']:
        if old_blocks is None:
            old_blocks = []
        unused_squares = {square
                          for row in grid.squares
                          for square in row
                          if square is not None}
        square_lists = defaultdict(list)
        lines = text.splitlines()
        while len(old_blocks) < len(lines):
            old_blocks.append([])
        for y, line in enumerate(lines):
            old_row = old_blocks[y]
            while len(old_row) < len(line):
                old_row.append(Block.UNUSED)
            for x, marker in enumerate(line):
                if marker == '?':
                    old_row[x] = marker
                    continue
                if marker == '#':
                    marker = old_row[x]
                    if marker is Block.UNUSED:
                        continue
                try:
                    old_square = grid[x, y]
                except IndexError:
                    continue
                if old_square is None:
                    continue
                old_row[x] = marker
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

    def draw(self, painter: QPainter, is_packed=False):
        self.transform_painter(painter, 1)
        square_positions = self.square_positions
        size = self.squares[0].size
        old_pen = painter.pen()
        divider_pen = QPen(self.divider_colour)
        divider_pen.setWidth(size // 33)
        for square in self.squares:
            square.draw(painter, is_packed=is_packed)
            x = square.x
            y = square.y
            painter.setPen(divider_pen)
            if (round(x), round(y-size)) in square_positions:
                if is_packed or self.tab_count:
                    painter.drawLine(x+size/4, y, x+size*3/4, y)
                else:
                    painter.drawLine(x, y, x + size, y)
            if (round(x-size), round(y)) in square_positions:
                if is_packed or self.tab_count:
                    painter.drawLine(x, y+size/4, x, y+size*3/4)
                else:
                    painter.drawLine(x, y, x, y+size)
            painter.setPen(old_pen)
        self.transform_painter(painter, -1)

        if not is_packed:
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

        square_size = self.squares[0].size
        length = max(abs(x2-x1), abs(y2-y1))
        cell_count = round(length / square_size)

        if (nick_radius == 0 and self.tab_count == 0) or cell_count == 0:
            painter.drawLine(x1, y1, x2, y2)
            return

        xstep = (x2-x1) / cell_count
        ystep = (y2-y1) / cell_count
        if xstep > 0:
            x0, y0 = x1, y1
            angle = 0
            step = xstep
        elif xstep < 0:
            x0, y0 = x2, y2
            angle = 0
            step = -xstep
        elif ystep > 0:
            x0, y0 = -y2, x2
            angle = -90
            step = ystep
        else:
            x0, y0 = -y1, x1
            angle = -90
            step = -ystep
        shortfall = round(square_size - step)
        path = QPainterPath(QPoint((shortfall-square_size)/2, 0))
        if self.tab_count == 0:
            path.lineTo(-nick_radius, 0)
            path.moveTo(nick_radius, 0)
            path.lineTo((square_size-shortfall)/2, 0)
        elif self.tab_count == 1:
            create_tab_path(path, square_size)
        else:
            create_double_tab_path(path, square_size, nick_radius)
        if shortfall:
            path.setElementPositionAt(path.elementCount() - 1,
                                      (square_size - shortfall)/2,
                                      0)
        path.translate((square_size - shortfall)/2, 0)
        painter.rotate(angle)
        path.translate(x0, y0)
        for i in range(cell_count):
            painter.drawPath(path)
            path.translate(step, 0)
        painter.rotate(-angle)

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
