import pytest
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from four_letter_blocks.square import Square
from tests.pixmap_differ import PixmapDiffer


@pytest.fixture(scope='session')
def qt_application() -> QApplication:
    return QApplication()


@pytest.fixture(scope='session')
def pixmap_differ(qt_application) -> PixmapDiffer:
    return PixmapDiffer()


def test_init():
    square = Square('X')

    assert square.letter == 'X'


def test_full_repr():
    square = Square('X', 12)

    assert repr(square) == "Square('X', 12)"


def test_repr():
    square = Square('X')

    assert repr(square) == "Square('X')"


def test_paint(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        180, 180,
        'test_square_paint')
    font = expected.font()
    expected.drawRect(20, 20, 80, 80)
    font.setPixelSize(60)
    expected.setFont(font)
    expected.drawText(20, 30, 80, 80, Qt.AlignHCenter, 'W')

    square = Square('W')
    square.move_to(60, 60)
    square.resize(80)

    square.draw(actual)
    pixmap_differ.assert_equal()


def test_paint_with_number(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        180, 180,
        'test_square_paint_with_number')
    font = expected.font()
    font.setPixelSize(20)
    expected.setFont(font)
    expected.drawRect(20, 20, 80, 80)
    expected.drawText(24, 20, 80, 80, 0, '12')
    font.setPixelSize(60)
    expected.setFont(font)
    expected.drawText(20, 30, 80, 80, Qt.AlignHCenter, 'W')

    square = Square('W', 12)
    square.move_to(60, 60)
    square.resize(80)

    square.draw(actual)
    pixmap_differ.assert_equal()
