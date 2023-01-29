from textwrap import dedent

from PySide6.QtGui import QPixmap, QPainter
from PySide6.QtWidgets import QApplication

from four_letter_blocks.puzzle import Puzzle
from tests.pixmap_differ import LiveQPainter


def draw_logo(width: int, height: int) -> QPixmap:
    pixmap = QPixmap(width, height)
    painter = QPainter(pixmap)
    try:
        painter.fillRect(painter.window(), 'cornsilk')
        grid_text = dedent("""\
            #FOUR#
            LETTER
            BLOCKS""")
        blocks_text = dedent("""\
            #CCAA#
            CCBDAA
            BBBDDD""")
        puzzle = Puzzle.parse_sections('',
                                       grid_text,
                                       '',
                                       blocks_text)
        square_size = min(width // 7, height // 4)
        puzzle.square_size = square_size
        puzzle.blocks[0].squares[1].number = None
        puzzle.blocks[0].squares[3].number = None
        puzzle.blocks[2].squares[0].number = 3
        puzzle.blocks[2].squares[1].number = None
        puzzle.blocks[2].squares[2].number = 4
        puzzle.blocks[1].squares[1].number = 2
        for block in puzzle.blocks:
            block.x += square_size // 2
            block.y += square_size // 2
            block.draw(painter, is_packed=True)
            block.draw_outline(painter)
    finally:
        painter.end()
    return pixmap


def demo():
    app = QApplication()
    width, height = 700, 400
    pixmap = draw_logo(width, height)
    LiveQPainter(pixmap, None).display((-width // 2, height // 2))
    app.exit(0)


def main():
    app = QApplication()
    pixmap = draw_logo(350, 200)
    pixmap.toImage().save('../docs/images/logo.png')
    app.exit(0)


if __name__ == '__main__':
    main()
elif __name__ == '__live_coding__':
    demo()
