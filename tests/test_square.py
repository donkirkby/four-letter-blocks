import pytest
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


def test_paint(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        180, 180,
        'test_square_paint')
    expected.drawRect(20, 20, 80, 80)

    square = Square('W')
    square.move_to(60, 60)
    square.resize(80)

    square.draw(actual)
    pixmap_differ.assert_equal()
