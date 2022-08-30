from PySide6.QtGui import QPainter, Qt, QColor

from four_letter_blocks.clue_painter import CluePainter
from tests.pixmap_differ import PixmapDiffer
from tests.test_puzzle import parse_basic_puzzle


# noinspection DuplicatedCode
def test_draw_clues(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()
    puzzle.down_clues[1].text_with_reference = "Run between 1 Across"

    width = 740
    height = 190
    margin = 10
    align_right = int(Qt.AlignRight)
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(
            width, height,
            'test_clue_painter_draw_clues') as (actual, expected):
        clue_painter = CluePainter(puzzle, font_size=20, margin=margin)
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
            'Clue numbers are shuffled: 1 Across might not be the top left. '
            '3 pieces.')
        line_height = CluePainter.find_text_height('X', expected)
        y += line_height
        expected.drawLine(margin, y + line_height//2,
                          width-margin, y + line_height//2)
        y += line_height
        expected.drawText(margin, y, width, height, 0, 'Across')
        expected.drawText(370, y, width, height, 0, 'Down')
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
        expected.drawText(370, y,
                          number_width, height,
                          align_right,
                          '1. ')
        expected.drawText(370, y+line_height,
                          number_width, height,
                          align_right,
                          '2. ')
        expected.drawText(370+number_width, y,
                          width, height,
                          0,
                          "Sour grapes\nRun between 1 Across")

        clue_painter.draw_page(actual)

    assert clue_painter.is_finished


# noinspection DuplicatedCode
def test_draw_clues_wrapped(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()

    puzzle.across_clues[0].text = 'Part of an extremely long, run-on sentence'
    width = 740
    height = 190
    margin = 10
    align_right = int(Qt.AlignRight)
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(
            width, height,
            'test_clue_painter_draw_clues_wrapped') as (actual, expected):
        clue_painter = CluePainter(puzzle, font_size=20, margin=margin)
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
            'Clue numbers are shuffled: 1 Across might not be the top left. '
            '3 pieces.')
        line_height = CluePainter.find_text_height('X', expected)
        y += line_height
        expected.drawLine(margin, y + line_height//2,
                          width-margin, y + line_height//2)
        y += line_height
        expected.drawText(margin, y, width, height, 0, 'Across')
        expected.drawText(370, y, width, height, 0, 'Down')
        y += line_height
        number_width = CluePainter.find_text_width('1. ', expected)
        expected.drawText(margin, y,
                          number_width, height,
                          align_right,
                          '1. ')
        expected.drawText(margin+number_width, y,
                          width, height,
                          0,
                          'Part of an extremely long, run-on\nsentence')
        expected.drawText(370, y,
                          number_width, height,
                          align_right,
                          '1. ')
        expected.drawText(370, y+line_height,
                          number_width, height,
                          align_right,
                          '2. ')
        expected.drawText(370+number_width, y,
                          width, height,
                          0,
                          'Sour grapes\nRun between words')

        clue_painter.draw_page(actual)

    assert not clue_painter.is_finished


# noinspection DuplicatedCode
def test_draw_clues_next_page(pixmap_differ: PixmapDiffer):
    puzzle1 = parse_basic_puzzle()
    puzzle1.across_clues[0].text = 'Part of an extremely long, run-on sentence'
    puzzle2 = parse_basic_puzzle()
    puzzle2.title = 'Next Puzzle'

    width = 740
    height = 190
    margin = 10
    align_right = int(Qt.AlignRight)
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(
            width, height,
            'test_clue_painter_draw_clues_next_page') as (actual, expected):
        clue_painter = CluePainter(puzzle1,
                                   puzzle2,
                                   font_size=20,
                                   margin=margin)
        font = expected.font()
        font.setPixelSize(20)
        expected.setFont(font)
        number_width = CluePainter.find_text_width('1. ', expected)
        expected.drawText(margin, margin,
                          number_width, height,
                          align_right,
                          '3. ')
        expected.drawText(margin+number_width, margin,
                          width, height,
                          0,
                          'One at a time')

        clue_painter.draw_page(actual)
        actual.fillRect(0, 0, width, height, 'white')
        clue_painter.draw_page(actual)


# noinspection DuplicatedCode
def test_draw_clues_with_suits(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()
    puzzle.across_clues[0].suit = 'D'
    puzzle.across_clues[1].suit = 'H'
    puzzle.down_clues[0].suit = 'C'
    puzzle.down_clues[1].suit = 'S'

    width = 740
    height = 190
    margin = 10
    align_right = int(Qt.AlignRight)
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(
            width, height,
            'test_clue_painter_draw_clues_with_suits') as (actual, expected):
        clue_painter = CluePainter(puzzle, font_size=20, margin=margin)
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
            'Clue numbers are shuffled: 1 Across might not be the top left. '
            '3 pieces.')
        line_height = CluePainter.find_text_height('X', expected)
        y += line_height
        expected.drawLine(margin, y + line_height//2,
                          width-margin, y + line_height//2)
        y += line_height
        expected.drawText(margin, y, width, height, 0, 'Across')
        expected.drawText(370, y, width, height, 0, 'Down')
        y += line_height
        number_width = CluePainter.find_text_width('1♡. ', expected)
        expected.drawText(margin, y,
                          number_width, height,
                          align_right,
                          '1♢. ')
        expected.drawText(margin, y+line_height,
                          number_width, height,
                          align_right,
                          '3♡. ')
        expected.drawText(margin+number_width, y,
                          width, height,
                          0,
                          'Part of a sentence\nOne at a time')
        expected.drawText(370, y,
                          number_width, height,
                          align_right,
                          '1♣. ')
        expected.drawText(370, y+line_height,
                          number_width, height,
                          align_right,
                          '2♠. ')
        expected.drawText(370+number_width, y,
                          width, height,
                          0,
                          'Sour grapes\nRun between words')

        clue_painter.draw_page(actual)


# noinspection DuplicatedCode
def test_draw_clues_first_clue_too_big(pixmap_differ: PixmapDiffer):
    puzzle1 = parse_basic_puzzle()
    puzzle1.across_clues[0].text = 'Part of an extremely long, run-on sentence'
    puzzle1.across_clues[1].text = 'Another extremely long, run-on sentence'
    puzzle2 = parse_basic_puzzle()
    puzzle2.title = 'Next Puzzle'

    width = 740
    height = 190
    margin = 10
    align_right = int(Qt.AlignRight)
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(
            width, height,
            'test_clue_painter_draw_clues_first_clue_too_big') as (actual, expected):
        clue_painter = CluePainter(puzzle1,
                                   puzzle2,
                                   font_size=20,
                                   margin=margin)
        font = expected.font()
        font.setPixelSize(20)
        expected.setFont(font)
        number_width = CluePainter.find_text_width('1. ', expected)
        expected.drawText(margin, margin,
                          number_width, height,
                          align_right,
                          '3. ')
        expected.drawText(margin+number_width, margin,
                          width, height,
                          0,
                          'Another extremely long, run-on\nsentence')

        clue_painter.draw_page(actual)
        actual.fillRect(0, 0, width, height, 'white')
        clue_painter.draw_page(actual)


# noinspection DuplicatedCode
def test_draw_clues_face_colour(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()
    puzzle.face_colour = QColor('lightgray')

    width = 740
    height = 190
    margin = 10
    align_right = int(Qt.AlignRight)
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(
            width, height,
            'test_clue_painter_draw_clues_face_colour') as (actual, expected):
        clue_painter = CluePainter(puzzle, font_size=20, margin=margin)
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
            'Clue numbers are shuffled: 1 Across might not be the top left. '
            '3 pieces.')
        line_height = CluePainter.find_text_height('X', expected)
        y += line_height
        expected.drawLine(margin, y + line_height//2,
                          width-margin, y + line_height//2)
        y += line_height
        expected.drawText(margin, y, width, height, 0, 'Across')
        expected.drawText(370, y, width, height, 0, 'Down')
        y += line_height
        number_width = CluePainter.find_text_width('1. ', expected)
        space_width = CluePainter.find_text_width(' ', expected)
        shading_width = number_width - space_width//2
        clue_height = CluePainter.find_text_height('P\nO', expected)
        expected.fillRect(margin, y, shading_width, clue_height, 'lightgray')
        expected.fillRect(370, y, shading_width, clue_height, 'lightgray')
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
        expected.drawText(370, y,
                          number_width, height,
                          align_right,
                          '1. ')
        expected.drawText(370, y+line_height,
                          number_width, height,
                          align_right,
                          '2. ')
        expected.drawText(370+number_width, y,
                          width, height,
                          0,
                          "Sour grapes\nRun between words")

        clue_painter.draw_page(actual)


# noinspection DuplicatedCode
def test_draw_clues_long_title(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()
    puzzle.title = 'Long Title That Will Not Fit (1000x2000)'

    width = 740
    height = 250
    margin = 10
    align_right = int(Qt.AlignRight)
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(
            width, height,
            'test_clue_painter_draw_clues_long_title') as (actual, expected):
        clue_painter = CluePainter(puzzle, font_size=20, margin=margin)
        font = expected.font()
        font.setPixelSize(40)
        expected.setFont(font)
        expected.drawText(0, margin,
                          width, height,
                          Qt.AlignHCenter,
                          'Long Title That Will Not Fit\n(1000x2000)')
        y = margin + CluePainter.find_text_height('X\n', expected)
        font.setPixelSize(20)
        expected.setFont(font)
        expected.drawText(
            margin, y,
            width, height,
            0,
            'Clue numbers are shuffled: 1 Across might not be the top left. '
            '3 pieces.')
        line_height = CluePainter.find_text_height('X', expected)
        y += line_height
        expected.drawLine(margin, y + line_height//2,
                          width-margin, y + line_height//2)
        y += line_height
        expected.drawText(margin, y, width, height, 0, 'Across')
        expected.drawText(370, y, width, height, 0, 'Down')
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
        expected.drawText(370, y,
                          number_width, height,
                          align_right,
                          '1. ')
        expected.drawText(370, y+line_height,
                          number_width, height,
                          align_right,
                          '2. ')
        expected.drawText(370+number_width, y,
                          width, height,
                          0,
                          "Sour grapes\nRun between words")

        clue_painter.draw_page(actual)


# noinspection DuplicatedCode
def test_draw_clues_intro(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()

    width = 740
    height = 190
    margin = 10
    align_right = int(Qt.AlignRight)
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(
            width, height,
            'test_clue_painter_draw_clues_intro') as (actual, expected):
        clue_painter = CluePainter(puzzle,
                                   font_size=20,
                                   margin=margin,
                                   intro_text='Introduction...')
        font = expected.font()
        font.setPixelSize(20)
        expected.setFont(font)
        line_height = CluePainter.find_text_height('X', expected)
        expected.drawText(margin, margin,
                          width, height,
                          0,
                          'Introduction...')
        y = margin + line_height
        font.setPixelSize(40)
        expected.setFont(font)
        expected.drawText(0, y,
                          width, height,
                          Qt.AlignHCenter,
                          'Basic Puzzle')
        y += CluePainter.find_text_height('X', expected)
        font.setPixelSize(20)
        expected.setFont(font)
        expected.drawText(
            margin, y,
            width, height,
            0,
            'Clue numbers are shuffled: 1 Across might not be the top left.'
            ' 3 pieces.')
        y += line_height
        expected.drawLine(margin, y + line_height//2,
                          width-margin, y + line_height//2)
        y += line_height
        expected.drawText(margin, y, width, height, 0, 'Across')
        expected.drawText(370, y, width, height, 0, 'Down')
        y += line_height
        number_width = CluePainter.find_text_width('1. ', expected)
        expected.drawText(margin, y,
                          number_width, height,
                          align_right,
                          '1. ')
        expected.drawText(margin+number_width, y,
                          width, height,
                          0,
                          'Part of a sentence')
        expected.drawText(370, y,
                          number_width, height,
                          align_right,
                          '1. ')
        expected.drawText(370+number_width, y,
                          width, height,
                          0,
                          "Sour grapes")

        clue_painter.draw_page(actual)


# noinspection DuplicatedCode
def test_draw_clues_footer(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()

    width = 740
    height = 190
    margin = 10
    align_right = int(Qt.AlignRight)
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(
            width, height,
            'test_clue_painter_draw_clues_footer') as (actual, expected):
        clue_painter = CluePainter(puzzle,
                                   font_size=20,
                                   margin=margin,
                                   footer_text='https://example.com')
        font = expected.font()
        font.setPixelSize(20)
        expected.setFont(font)
        line_height = CluePainter.find_text_height('X', expected)
        expected.drawText(0, height-margin-line_height,
                          width, height,
                          Qt.AlignHCenter,
                          'https://example.com')
        y = margin
        font.setPixelSize(40)
        expected.setFont(font)
        expected.drawText(0, y,
                          width, height,
                          Qt.AlignHCenter,
                          'Basic Puzzle')
        y += CluePainter.find_text_height('X', expected)
        font.setPixelSize(20)
        expected.setFont(font)
        expected.drawText(
            margin, y,
            width, height,
            0,
            'Clue numbers are shuffled: 1 Across might not be the top left.'
            ' 3 pieces.')
        y += line_height
        expected.drawLine(margin, y + line_height//2,
                          width-margin, y + line_height//2)
        y += line_height
        expected.drawText(margin, y, width, height, 0, 'Across')
        expected.drawText(370, y, width, height, 0, 'Down')
        y += line_height
        number_width = CluePainter.find_text_width('1. ', expected)
        expected.drawText(margin, y,
                          number_width, height,
                          align_right,
                          '1. ')
        expected.drawText(margin+number_width, y,
                          width, height,
                          0,
                          'Part of a sentence')
        expected.drawText(370, y,
                          number_width, height,
                          align_right,
                          '1. ')
        expected.drawText(370+number_width, y,
                          width, height,
                          0,
                          "Sour grapes")

        clue_painter.draw_page(actual)
