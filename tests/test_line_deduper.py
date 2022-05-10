from PySide6.QtGui import QPen

from four_letter_blocks.line_deduper import LineDeduper
from tests.pixmap_differ import PixmapDiffer


# noinspection DuplicatedCode
def test_simple(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        400, 180,
        'test_line_deduper_simple')

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

    pixmap_differ.assert_equal()


# noinspection DuplicatedCode
def test(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        400, 180,
        'test_line_deduper')

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

    pixmap_differ.assert_equal()
