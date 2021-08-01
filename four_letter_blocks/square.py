from PySide6.QtCore import QRect, Qt
from PySide6.QtGui import QPainter


class Square:
    NUMBER_SIZE = 0.25
    LETTER_SIZE = 0.75

    def __init__(self, letter: str, number: int = None):
        self.letter = letter
        self.number = number
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
