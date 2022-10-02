from PySide6.QtGui import QPen, QPainter, QPainterPath

from four_letter_blocks.line_deduper import LineDeduper
from tests.pixmap_differ import PixmapDiffer


# noinspection DuplicatedCode
def test_simple(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(400, 180) as (actual, expected):
        pen1 = QPen('brown')
        pen1.setWidth(11)
        pen2 = QPen('yellow')
        pen2.setWidth(3)

        expected.setPen(pen1)
        expected.drawLine(100, 50, 200, 50)

        deduper = LineDeduper(actual)
        deduper.setPen(pen1)
        deduper.drawLine(100, 50, 200, 50)
        deduper.setPen(pen2)
        deduper.drawLine(100, 50, 200, 50)


# noinspection DuplicatedCode
def test_translate(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(400, 180) as (actual, expected):
        pen1 = QPen('brown')
        pen1.setWidth(11)
        pen2 = QPen('yellow')
        pen2.setWidth(3)

        expected.setPen(pen1)
        expected.drawLine(100, 50, 200, 50)

        deduper = LineDeduper(actual)
        deduper.setPen(pen1)
        deduper.drawLine(100, 50, 200, 50)

        deduper.translate(20, 0)
        deduper.setPen(pen2)
        deduper.drawLine(80, 50, 180, 50)


# noinspection DuplicatedCode
def test_path(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(400, 180) as (actual, expected):
        path1 = QPainterPath()
        path1.lineTo(20, 10)
        path1.cubicTo(20, 15, 50, 30, 100, 30)
        path1.translate(50, 50)
        pen1 = QPen('brown')
        pen2 = QPen('blue')

        expected.setPen(pen1)
        expected.drawPath(path1)
        expected.rotate(30)
        expected.setPen(pen2)
        expected.drawPath(path1)

        deduper = LineDeduper(actual)
        deduper.setPen(pen1)
        deduper.drawPath(path1)
        deduper.setPen(pen2)
        deduper.drawPath(path1)

        deduper.rotate(30)
        deduper.drawPath(path1)
