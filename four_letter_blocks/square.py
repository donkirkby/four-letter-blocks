from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPainter, QColor, QPainterPath, QLinearGradient, QRadialGradient

from four_letter_blocks.suit import Suit


class Square:
    NUMBER_SIZE = 0.25
    LETTER_SIZE = 0.75
    SUIT_DISPLAYS = {'C': Suit('♣'),
                     'D': Suit('♢', '♦'),
                     'H': Suit('♡', '♥'),
                     'S': Suit('♠'),
                     None: Suit('')}

    def __init__(self, letter: str, number: int = None, suit: str = None):
        self.letter = letter
        self.number = number
        self.suit = suit
        self.x = self.y = 0
        self.size = 1
        self.across_word = self.down_word = None
        self.face_colour = QColor('transparent')

    def __repr__(self):
        if self.number is None:
            number_repr = ''
        else:
            number_repr = f", {self.number}"
        return f"Square({self.letter!r}{number_repr})"

    def draw(self, painter: QPainter, is_packed=False):
        pen = painter.pen()
        pen.setWidth(round(self.size/80))
        painter.setPen(pen)
        rect = QRect(self.x,
                     self.y,
                     self.size,
                     self.size)
        face = QColor(self.face_colour)
        black = QColor('black')
        suit_outline = QColor(140, 140, 140)
        suit_fill = QColor(227, 227, 227)
        font = painter.font()

        if is_packed:
            draw_gradient_rect(painter,
                               face,
                               self.x + self.size / 16, self.y + self.size / 16,
                               self.size * 7 / 8, self.size * 7 / 8,
                               self.size * 5 / 16)
        else:
            painter.fillRect(self.x, self.y, self.size, self.size, face)

        font.setPixelSize(self.size)
        if self.suit is None:
            pass
        elif not is_packed:
            suit_display = self.SUIT_DISPLAYS[self.suit]
            painter.setFont(font)
            old_pen = painter.pen()
            if suit_display.filled != suit_display.display:
                painter.setPen(suit_fill)
                painter.drawText(rect, Qt.AlignHCenter, suit_display.filled)
            painter.setPen(suit_outline)
            painter.drawText(rect, Qt.AlignHCenter, suit_display.display)
            painter.setPen(old_pen)
        else:
            x = rect.left() + self.size / 2
            y = rect.top() + self.size * 0.775
            suit_display = self.SUIT_DISPLAYS[self.suit]
            font.setPixelSize(self.size * 0.82)
            painter.setFont(font)
            if suit_display.filled != suit_display.display:
                painter.setPen(suit_fill)
                draw_text_path(painter,
                               x,
                               y,
                               suit_display.filled,
                               is_centred=True)
            painter.setPen(suit_outline)
            draw_text_path(painter,
                           x,
                           y,
                           suit_display.display,
                           is_centred=True)
            painter.setPen(black)

        if self.number is None:
            pass
        elif not is_packed:
            font.setPixelSize(self.size * self.NUMBER_SIZE)
            number_shift = round(self.size / 20)
            painter.setFont(font)
            rect.translate(number_shift, 0)
            painter.drawText(rect, 0, str(self.number))
            rect.translate(-number_shift, 0)
        else:
            font.setPixelSize(self.size * 0.1875)
            painter.setFont(font)
            draw_text_path(painter,
                           rect.left()+self.size*0.225,
                           rect.top()+self.size*0.3625,
                           str(self.number))

        if not is_packed:
            font.setPixelSize(self.size * self.LETTER_SIZE)
            letter_shift = round(self.size * (1 - self.LETTER_SIZE) / 2)
            painter.setFont(font)
            rect.translate(0, letter_shift)
            painter.drawText(rect, Qt.AlignHCenter, self.letter)
            rect.translate(0, -letter_shift)
        else:
            font.setPixelSize(self.size * 0.57)
            painter.setFont(font)
            draw_text_path(painter,
                           rect.left()+self.size/2,
                           rect.top() + self.size*0.775,
                           self.letter,
                           is_centred=True)

    def display_number(self):
        suit_display = self.SUIT_DISPLAYS[self.suit]
        number_display = f'{self.number}{suit_display.display}'
        return number_display


def draw_text_path(painter: QPainter,
                   x: float,
                   y: float,
                   text: str,
                   is_centred: bool = False):
    path = QPainterPath()
    font = painter.font()
    path.addText(x, y, font, text)
    if is_centred:
        rect = path.boundingRect()
        path.translate(x-(rect.left()+rect.right())/2, 0)

    old_hint = painter.testRenderHint(QPainter.Antialiasing)
    painter.setRenderHint(QPainter.Antialiasing)
    painter.fillPath(path, painter.pen().color())
    painter.setRenderHint(QPainter.Antialiasing, old_hint)


# noinspection DuplicatedCode
def draw_gradient_rect(painter: QPainter,
                       colour: QColor,
                       x: float,
                       y: float,
                       width: float,
                       height: float,
                       radius: float):
    if colour.alpha() == 0:
        return
    x0 = round(x)
    x1 = round(x + radius)
    x2 = round(x + width - radius)
    x3 = round(x + width)
    y0 = round(y)
    y1 = round(y + radius)
    y2 = round(y + height - radius)
    y3 = round(y + height)

    # left
    gradient = QLinearGradient()
    gradient.setStart(x0, y0)
    gradient.setFinalStop(x1, y0)
    white = QColor(255, 255, 255, 0)
    gradient.setStops(((0, white), (1, colour)))
    painter.fillRect(x0, y1, x1 - x0, y2 - y1, gradient)

    # right
    gradient.setStart(x3, y0)
    gradient.setFinalStop(x2, y0)
    painter.fillRect(x2, y1, x3 - x2, y2 - y1, gradient)

    # top
    gradient.setStart(x0, y0)
    gradient.setFinalStop(x0, y1)
    painter.fillRect(x1, y0, x2 - x1, y2 - y0, gradient)

    # bottom
    gradient.setStart(x0, y3)
    gradient.setFinalStop(x0, y2)
    painter.fillRect(x1, y2, x2 - x1, y3 - y2, gradient)

    # top left
    gradient = QRadialGradient()
    gradient.setStops(((0, colour), (1, white)))
    gradient.setRadius(radius)
    gradient.setCenter(x1, y1)
    gradient.setFocalPoint(gradient.center())
    painter.fillRect(x0, y0, x1-x0, y1-y0, gradient)

    # top right
    gradient.setCenter(x2, y1)
    gradient.setFocalPoint(gradient.center())
    painter.fillRect(x2, y0, x3 - x2, y1 - y0, gradient)

    # bottom left
    gradient.setCenter(x1, y2)
    gradient.setFocalPoint(gradient.center())
    painter.fillRect(x0, y2, x1 - x0, y3 - y2, gradient)

    # bottom right
    gradient.setCenter(x2, y2)
    gradient.setFocalPoint(gradient.center())
    painter.fillRect(x2, y2, x3 - x2, y3 - y2, gradient)
