from PySide6.QtGui import QPainter, Qt

from four_letter_blocks.clue_painter import CluePainter
from tests.pixmap_differ import PixmapDiffer
from tests.test_puzzle import parse_basic_puzzle


def test_draw_clues(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()

    width = 640
    height = 180
    margin = 10
    font_size = 20
    title_size = 40
    clue_painter = CluePainter(puzzle, font_size=font_size, margin=margin)
    align_right = int(Qt.AlignRight)
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(
            width, height,
            'test_clue_painter_draw_clues') as (actual, expected):
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
            margin, 54,
            width, height,
            0,
            'Clue numbers are shuffled: 1 Across might not be in the top left.')
        expected.drawLine(margin, 86,
                          width-margin, 86)
        expected.drawText(margin, 96, width, height, 0, 'Across')
        expected.drawText(320, 96, width, height, 0, 'Down')
        expected.drawText(margin, 120, 16, height, align_right, '1.')
        expected.drawText(26, 120, width, height, 0, 'Part of a sentence')
        expected.drawText(margin, 143, 16, height, align_right, '3.')
        expected.drawText(26, 143, width, height, 0, 'One at a time')
        expected.drawText(320, 120, 16, height, align_right, '1.')
        expected.drawText(336, 120, width, height, 0, 'Sour grapes')
        expected.drawText(320, 143, 16, height, align_right, '2.')
        expected.drawText(336, 143, width, height, 0, 'Run between words')

        actual.fillRect(0, 0, width, height, 'ivory')
        clue_painter.draw_page(actual)
