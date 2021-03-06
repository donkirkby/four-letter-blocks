from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor

from four_letter_blocks.square import Square
from tests.pixmap_differ import PixmapDiffer


def test_init():
    square = Square('X')

    assert square.letter == 'X'


def test_full_repr():
    square = Square('X', 12)

    assert repr(square) == "Square('X', 12)"


def test_repr():
    square = Square('X')

    assert repr(square) == "Square('X')"


# noinspection DuplicatedCode
def test_paint(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        180, 180,
        'test_square_paint')
    font = expected.font()
    font.setPixelSize(60)
    expected.setFont(font)
    expected.drawText(20, 30, 80, 80, Qt.AlignHCenter, 'W')

    square = Square('W')
    square.x = 20
    square.y = 20
    square.size = 80

    square.draw(actual)

    expected.drawRect(20, 20, 80, 80)
    actual.drawRect(20, 20, 80, 80)

    pixmap_differ.assert_equal()


# noinspection DuplicatedCode
def test_paint_with_number(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        180, 180,
        'test_square_paint_with_number')
    font = expected.font()
    font.setPixelSize(20)
    expected.setFont(font)
    expected.drawText(24, 20, 80, 80, 0, '12')
    font.setPixelSize(60)
    expected.setFont(font)
    expected.drawText(20, 30, 80, 80, Qt.AlignHCenter, 'W')

    square = Square('W', 12)
    square.x = 20
    square.y = 20
    square.size = 80

    square.draw(actual)

    expected.drawRect(20, 20, 80, 80)
    actual.drawRect(20, 20, 80, 80)

    pixmap_differ.assert_equal()


# noinspection DuplicatedCode
def test_paint_with_number_and_suit(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        180, 180,
        'test_square_paint_with_number_and_suit')
    font = expected.font()
    font.setPixelSize(80)
    expected.setFont(font)
    gray1 = 227
    gray2 = 166
    expected.setPen(QPen(QColor(gray1, gray1, gray1)))
    expected.drawText(20, 20, 80, 80, Qt.AlignHCenter, '♥')
    expected.setPen(QPen(QColor(gray2, gray2, gray2)))
    expected.drawText(20, 20, 80, 80, Qt.AlignHCenter, '♡')
    expected.setPen(QPen('black'))
    font.setPixelSize(20)
    expected.setFont(font)
    expected.drawText(24, 20, 80, 80, 0, '12')
    font.setPixelSize(60)
    expected.setFont(font)
    expected.drawText(20, 30, 80, 80, Qt.AlignHCenter, 'W')

    square = Square('W', 12, 'H')
    square.x = 20
    square.y = 20
    square.size = 80

    square.draw(actual)

    expected.drawRect(20, 20, 80, 80)
    actual.drawRect(20, 20, 80, 80)

    pixmap_differ.assert_equal()


# noinspection DuplicatedCode
def test_paint_path(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(180, 180, 'test_paint_path')
    actual.drawText = lambda *args: None  # Check that all text converts to path

    square = Square('W', 12, 'H')
    square.x = 20
    square.y = 20
    square.size = 80
    square.draw(expected)

    square.draw(actual, use_text=False)

    pixmap_differ.compare()
    assert pixmap_differ.diff_count <= 800
