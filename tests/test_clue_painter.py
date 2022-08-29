from PySide6.QtGui import QPainter, Qt

from four_letter_blocks.clue_painter import CluePainter
from tests.pixmap_differ import PixmapDiffer
from tests.test_puzzle import parse_basic_puzzle


def test_draw_clues(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()

    width = 680
    height = 180
    margin = 10
    align_right = int(Qt.AlignRight)
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(
            width, height,
            'test_clue_painter_draw_clues') as (actual, expected):
        clue_painter = CluePainter(puzzle, font_size=20, margin=margin)
        expected.fillRect(0, 0, width, height, 'ivory')
        font = expected.font()
        font.setPixelSize(40)
        expected.setFont(font)
        expected.drawText(0, margin,
                          width, height,
                          Qt.AlignHCenter,
                          'Basic Puzzle')
        y = margin + CluePainter.find_text_height('X', expected)
        font.setPixelSize(20)
        expected.setFont(font)
        expected.drawText(
            margin, y,
            width, height,
            0,
            'Clue numbers are shuffled: 1 Across might not be in the top left.')
        line_height = CluePainter.find_text_height('X', expected)
        y += line_height
        expected.drawLine(margin, y + line_height//2,
                          width-margin, y + line_height//2)
        y += line_height
        expected.drawText(margin, y, width, height, 0, 'Across')
        expected.drawText(340, y, width, height, 0, 'Down')
        y += line_height
        number_width = CluePainter.find_text_width('1. ', expected)
        expected.drawText(margin, y,
                          number_width, height,
                          align_right,
                          '1. ')
        expected.drawText(margin, y+line_height,
                          number_width, height,
                          align_right,
                          '3. ')
        expected.drawText(margin+number_width, y,
                          width, height,
                          0,
                          'Part of a sentence\nOne at a time')
        expected.drawText(340, y,
                          number_width, height,
                          align_right,
                          '1. ')
        expected.drawText(340, y+line_height,
                          number_width, height,
                          align_right,
                          '2. ')
        expected.drawText(340+number_width, y,
                          width, height,
                          0,
                          'Sour grapes\nRun between words')

        actual.fillRect(0, 0, width, height, 'ivory')
        clue_painter.draw_page(actual)
