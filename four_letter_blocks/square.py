from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPainter, QColor, QBrush

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

    def __repr__(self):
        if self.number is None:
            number_repr = ''
        else:
            number_repr = f", {self.number}"
        return f"Square({self.letter!r}{number_repr})"

    def draw(self, painter: QPainter):
        pen = painter.pen()
        pen.setWidth(round(self.size/80))
        painter.setPen(pen)
        rect = QRect(self.x,
                     self.y,
                     self.size,
                     self.size)
        white = QColor('white')
        painter.setBrush(QBrush(white))
        painter.drawRect(rect)
        font = painter.font()
        number_shift = round(self.size / 20)
        letter_shift = round(self.size * (1 - self.LETTER_SIZE)/2)
        rect.translate(number_shift, 0)
        if self.number is not None:
            font.setPixelSize(self.size * self.NUMBER_SIZE)
            painter.setFont(font)
            painter.drawText(rect, 0, str(self.number))
        rect.translate(-number_shift, letter_shift)

        font.setPixelSize(self.size * self.LETTER_SIZE)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignHCenter, self.letter)

        rect.translate(0, -letter_shift)
        if self.suit is not None:
            suit_display = self.SUIT_DISPLAYS[self.suit]
            font.setPixelSize(self.size)
            painter.setFont(font)
            old_pen = painter.pen()
            painter.setPen(QColor(0, 0, 0, 30))
            painter.drawText(rect, Qt.AlignHCenter, suit_display.filled)
            painter.setPen(QColor(0, 0, 0, 70))
            painter.drawText(rect, Qt.AlignHCenter, suit_display.display)
            painter.setPen(old_pen)

    def display_number(self):
        suit_display = self.SUIT_DISPLAYS[self.suit]
        number_display = f'{self.number}{suit_display.display}'
        return number_display
