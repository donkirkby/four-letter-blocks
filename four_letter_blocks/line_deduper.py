import typing

from PySide6.QtGui import QPainter, QPainterPath


class LineDeduper:
    """ Wrap a QPainter, and skip duplicate lines. """
    def __init__(self, painter: QPainter):
        self.painter = painter
        self.line_ends: typing.Set[typing.Tuple[int, int, int, int]] = set()
        self.path_points: typing.Set[
            typing.Tuple[typing.Tuple[int, int], ...]] = set()

    def __getattr__(self, item):
        return getattr(self.painter, item)

    # noinspection PyPep8Naming
    def drawLine(self, x1: int, y1: int, x2: int, y2: int):
        transform = self.painter.transform()
        x3: int
        y3: int
        x3, y3 = transform.map(x1, y1)  # type:ignore[misc]
        x4: int
        y4: int
        x4, y4 = transform.map(x2, y2)  # type:ignore[misc]
        ends = (x3, y3, x4, y4)
        if ends not in self.line_ends:
            self.painter.drawLine(x1, y1, x2, y2)
            self.line_ends.add(ends)

    # noinspection PyPep8Naming
    def drawPath(self, path: QPainterPath):
        elements = (path.elementAt(i)
                    for i in range(path.elementCount()))
        raw_points = ((element.x, element.y)  # type:ignore[attr-defined]
                      for element in elements)
        transform = self.painter.transform()
        points: typing.Generator[typing.Tuple[float, float], None, None] = (
            transform.map(x, y)  # type:ignore[misc]
            for x, y in raw_points)
        rounded_points = tuple((round(x), round(y))
                               for x, y in points)
        if rounded_points not in self.path_points:
            self.painter.drawPath(path)
            self.path_points.add(rounded_points)
