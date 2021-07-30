from PySide6.QtGui import QPainter


class Square:
    def __init__(self, letter: str):
        self.letter = letter
        self.x = self.y = 0
        self.size = 100

    def move_to(self, x: int, y: int):
        self.x = x
        self.y = y

    def resize(self, size: int):
        self.size = size

    def draw(self, painter: QPainter):
        painter.drawRect(self.x - self.size//2,
                         self.y - self.size//2,
                         self.size,
                         self.size)
