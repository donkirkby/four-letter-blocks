from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPainter, QColor, QPainterPath

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
        self.face_colour = QColor('white')

    def __repr__(self):
        if self.number is None:
            number_repr = ''
        else:
            number_repr = f", {self.number}"
        return f"Square({self.letter!r}{number_repr})"

    def draw(self, painter: QPainter, use_text=True):
        pen = painter.pen()
        pen.setWidth(round(self.size/80))
        painter.setPen(pen)
        rect = QRect(self.x,
                     self.y,
                     self.size,
                     self.size)
        face = QColor(self.face_colour)
        black = QColor('black')
        suit_outline = QColor(166, 166, 166)
        suit_fill = QColor(227, 227, 227)
        font = painter.font()

        number_shift = round(self.size / 20)
        letter_shift = round(self.size * (1 - self.LETTER_SIZE)/2)

        painter.fillRect(rect, face)

        font.setPixelSize(self.size)
        if self.suit is None:
            pass
        elif use_text:
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
            offset = (rect.left()+self.size*0.051, rect.top()+self.size*0.93)
            suit_display = self.SUIT_DISPLAYS[self.suit]
            path = QPainterPath()
            if suit_display.filled != suit_display.display:
                path.addText(0, 0, font, suit_display.filled)
                path.translate(*offset)
                painter.fillPath(path, suit_fill)
                path.clear()
            path.addText(0, 0, font, suit_display.display)
            path.translate(*offset)
            painter.fillPath(path, suit_outline)

        font.setPixelSize(self.size * self.NUMBER_SIZE)
        if self.number is None:
            pass
        elif use_text:
            painter.setFont(font)
            rect.translate(number_shift, 0)
            painter.drawText(rect, 0, str(self.number))
            rect.translate(-number_shift, 0)
        else:
            path = QPainterPath()
            path.addText(0, 0, font, str(self.number))
            path.translate(rect.left()+self.size*0.05,
                           rect.top()+self.size*0.225)
            painter.fillPath(path, black)

        font.setPixelSize(self.size * self.LETTER_SIZE)
        if use_text:
            painter.setFont(font)
            rect.translate(0, letter_shift)
            painter.drawText(rect, Qt.AlignHCenter, self.letter)
            rect.translate(0, -letter_shift)
        else:
            path = QPainterPath()
            path.addText(0, 0, font, self.letter)
            letter_rect = path.boundingRect()
            path.translate(
                rect.left()-letter_rect.left() +
                (rect.width()-letter_rect.width())/2,
                rect.top() + self.size*0.824)
            painter.fillPath(path, black)

    def display_number(self):
        suit_display = self.SUIT_DISPLAYS[self.suit]
        number_display = f'{self.number}{suit_display.display}'
        return number_display
