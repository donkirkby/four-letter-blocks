from PySide6.QtCore import Qt
from PySide6.QtGui import QPen, QColor, QPainter, QRadialGradient, QLinearGradient, QPainterPath

from four_letter_blocks.square import Square, draw_gradient_rect, draw_text_path
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
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(180, 180) as (actual, expected):
        for painter in (actual, expected):
            painter.fillRect(0, 0, 180, 180, 'ivory')
        expected.fillRect(20, 20, 80, 80, 'white')
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


def test_gradient_rect(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(380, 180) as (actual, expected):
        expected.fillRect(0, 0, 380, 180, 'cornsilk')
        gradient = QLinearGradient()
        gradient.setStart(12.5, 0)
        gradient.setFinalStop(37.5, 0)
        white = QColor(255, 255, 255, 0)
        face_colour = QColor.fromHsv(120, 50, 255)
        gradient.setStops(((0, white), (1, face_colour)))
        expected.fillRect(12.5, 37.5, 38, 25, gradient)

        gradient.setStart(87.5, 0)
        gradient.setFinalStop(62.5, 0)
        expected.fillRect(50, 37.5, 37.5, 25, gradient)

        gradient.setStart(0, 12.5)
        gradient.setFinalStop(0, 37.5)
        expected.fillRect(37.5, 12.5, 25, 38, gradient)

        gradient.setStart(0, 87.5)
        gradient.setFinalStop(0, 62.5)
        expected.fillRect(37.5, 50, 25, 37.5, gradient)

        gradient = QRadialGradient()
        gradient.setStops(((0, face_colour), (1, white)))
        gradient.setRadius(25)
        gradient.setCenter(37.5, 37.5)
        gradient.setFocalPoint(gradient.center())
        expected.fillRect(12.5, 12.5, 25, 25, gradient)

        gradient.setCenter(62.5, 37.5)
        gradient.setFocalPoint(gradient.center())
        expected.fillRect(62.5, 12.5, 25, 25, gradient)

        gradient.setCenter(37.5, 62.5)
        gradient.setFocalPoint(gradient.center())
        expected.fillRect(12.5, 62.5, 25, 25, gradient)

        gradient.setCenter(62.5, 62.5)
        gradient.setFocalPoint(gradient.center())
        expected.fillRect(62.5, 62.5, 25, 25, gradient)

        actual.fillRect(0, 0, 380, 180, 'cornsilk')
        draw_gradient_rect(actual, face_colour, 12.5, 12.5, 75, 75, radius=25)


def test_draw_text_path(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(380, 180) as (actual, expected):
        for painter in (expected, actual):
            painter.drawLine(50, 105, 50, 125)

        path = QPainterPath()
        font = expected.font()
        font.setPixelSize(40)
        x = 50
        y = 100
        path.addText(x, y, font, '42')
        rect = path.boundingRect()
        path.translate(50 - (rect.left()+rect.right())/2, 0)
        expected.fillPath(path, QColor('blue'))

        actual.setFont(font)
        actual.setPen(QColor('blue'))
        draw_text_path(actual, x, y, '42', is_centred=True)


# noinspection DuplicatedCode
def test_paint_with_face_colour(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(180, 180) as (actual, expected):
        face_colour = QColor.fromHsv(120, 50, 255)
        draw_gradient_rect(expected,
                           face_colour,
                           25, 25, 70, 70, 25)
        font = expected.font()
        expected.setPen(QPen('black'))
        font.setPixelSize(15)
        expected.setFont(font)
        draw_text_path(expected, 38, 49, '12')

        font.setPixelSize(45)
        expected.setFont(font)
        draw_text_path(expected, 60, 82, 'W', is_centred=True)

        square = Square('W', 12)
        square.x = 20
        square.y = 20
        square.size = 80
        square.face_colour = face_colour

        square.draw(actual, is_packed=True)

        for painter in (expected, actual):
            # Show cut line
            painter.drawRect(20, 20, 80, 80)

            # Show boundaries for drift
            painter.drawLine(0, 40, 15, 40)
            painter.drawLine(0, 80, 15, 80)
            painter.drawLine(40, 0, 40, 15)
            painter.drawLine(80, 0, 80, 15)


# noinspection DuplicatedCode
def test_paint_packed_with_suit(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(180, 180) as (actual, expected):
        font = expected.font()
        font.setPixelSize(65)
        expected.setFont(font)
        gray1 = 227
        gray2 = 166
        expected.setPen(QPen(QColor(gray1, gray1, gray1)))
        draw_text_path(expected, 60, 82, '♥', is_centred=True)
        expected.setPen(QPen(QColor(gray2, gray2, gray2)))
        draw_text_path(expected, 60, 82, '♡', is_centred=True)
        expected.setPen(QPen('black'))
        font.setPixelSize(15)
        expected.setFont(font)
        draw_text_path(expected, 38, 49, '12')

        font.setPixelSize(45)
        expected.setFont(font)
        draw_text_path(expected, 60, 82, 'W', is_centred=True)

        square = Square('W', 12, 'H')
        square.x = 20
        square.y = 20
        square.size = 80

        square.draw(actual, is_packed=True)

        for painter in (expected, actual):
            # Show cut line
            painter.drawRect(20, 20, 80, 80)

            # Show boundaries for drift
            painter.drawLine(0, 40, 15, 40)
            painter.drawLine(0, 80, 15, 80)
            painter.drawLine(40, 0, 40, 15)
            painter.drawLine(80, 0, 80, 15)
