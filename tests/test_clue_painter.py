from PySide6.QtGui import QPainter, Qt

from four_letter_blocks.clue_painter import CluePainter
from tests.pixmap_differ import PixmapDiffer
from tests.test_puzzle import parse_basic_puzzle


def test_draw_clues(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()

    width = 640
    height = 180
    margin = 10
    align_right = int(Qt.AlignRight)
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(
            width, height,
            'test_clue_painter_draw_clues') as (actual, expected):
        font_size = CluePainter.find_font_size(22, expected)
        title_size = CluePainter.find_font_size(44, expected)
        clue_painter = CluePainter(puzzle, font_size=22, margin=margin)
        expected.fillRect(0, 0, width, height, 'ivory')
        font = expected.font()
        font.setPixelSize(title_size)
        expected.setFont(font)
        expected.drawText(0, margin,
                          width, height,
                          Qt.AlignHCenter,
                          'Basic Puzzle')
        font.setPixelSize(font_size)
        expected.setFont(font)
        expected.drawText(
            margin, 53,
            width, height,
            0,
            'Clue numbers are shuffled: 1 Across might not be in the top left.')
        expected.drawLine(margin, 85,
                          width-margin, 85)
        expected.drawText(margin, 95, width, height, 0, 'Across')
        expected.drawText(320, 95, width, height, 0, 'Down')
        expected.drawText(margin, 119, 16, height, align_right, '1.\n3.')
        expected.drawText(26, 119,
                          width, height,
                          0,
                          ' Part of a sentence\n One at a time')
        expected.drawText(320, 119, 16, height, align_right, '1.\n2.')
        expected.drawText(336, 119,
                          width, height,
                          0,
                          ' Sour grapes\n Run between words')

        actual.fillRect(0, 0, width, height, 'ivory')
        clue_painter.draw_page(actual)
