from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter, Qt, QColor, QFont

from four_letter_blocks.clue_painter import CluePainter
from four_letter_blocks.puzzle import draw_rotated_tiles
from four_letter_blocks.puzzle_set import PuzzleSet
from four_letter_blocks.square import draw_gradient_rect
from tests.pixmap_differ import PixmapDiffer
from tests.test_puzzle import parse_basic_puzzle


# noinspection DuplicatedCode
def test_draw_text(pixmap_differ: PixmapDiffer):
    with pixmap_differ.create_painters(740, 190):
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter
        pixmap_differ.radius = 6
        pixmap_differ.tolerance = 26

        font = expected.font()
        font.setPixelSize(30)
        expected.setFont(font)

        expected.setRenderHint(QPainter.TextAntialiasing, False)
        expected.setRenderHint(QPainter.Antialiasing, False)
        expected.drawText(QRectF(10, 10, 300, 100),
                          0,
                          'Lorem ipsum\ndolores sit amet.')

        actual.setFont(font)

        rect = QRectF(10, 10, 300, 100)
        CluePainter.draw_text(rect, 'Lorem ipsum', actual)
        CluePainter.draw_text(rect, 'dolores sit amet.', actual)


# noinspection DuplicatedCode
def test_draw_text_bold(pixmap_differ: PixmapDiffer):
    with pixmap_differ.create_painters(740, 190):
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter
        pixmap_differ.radius = 6
        pixmap_differ.tolerance = 26

        font = expected.font()
        font.setPixelSize(30)
        bold_font = QFont(font)
        bold_font.setBold(True)
        expected.setFont(bold_font)

        expected.setRenderHint(QPainter.TextAntialiasing, False)
        expected.setRenderHint(QPainter.Antialiasing, False)
        expected.drawText(QRectF(10, 10, 300, 100),
                          0,
                          'Lorem ipsum\ndolores sit amet.')

        actual.setFont(font)

        rect = QRectF(10, 10, 300, 100)
        CluePainter.draw_text(rect,
                              'Lorem ipsum\ndolores sit amet.',
                              actual,
                              is_bold=True)


# noinspection DuplicatedCode
def test_draw_text_background(pixmap_differ: PixmapDiffer):
    with pixmap_differ.create_painters(740, 190):
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter
        pixmap_differ.radius = 6
        pixmap_differ.tolerance = 26

        font = expected.font()
        font.setPixelSize(30)
        expected.setFont(font)
        pen = expected.pen()
        pen.setWidth(1)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        expected.setPen(pen)
        padding = 3
        background_colour = QColor('burlywood')
        text_width = CluePainter.find_text_width('dolores sit amet.', expected)
        text_width += 2 * padding
        text_height = CluePainter.find_text_height('X\nX', expected)
        text_rect = QRectF(10, 10,
                           text_width, text_height + 2 * padding)
        expected.fillRect(text_rect, background_colour)
        expected.drawRect(text_rect)

        expected.setRenderHint(QPainter.TextAntialiasing, False)
        expected.setRenderHint(QPainter.Antialiasing, False)
        expected.drawText(QRectF(10+padding, 10+padding, 300-2*padding, 100),
                          0,
                          'Lorem ipsum\ndolores sit amet.')

        actual.setFont(font)

        rect = QRectF(10, 10, 300, 100)
        CluePainter.draw_text(rect,
                              'Lorem ipsum\ndolores sit amet.',
                              actual,
                              background=background_colour)


# noinspection DuplicatedCode
def test_draw_text_gradient(pixmap_differ: PixmapDiffer):
    with pixmap_differ.create_painters(740, 190):
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter
        pixmap_differ.radius = 6
        pixmap_differ.tolerance = 26

        font = expected.font()
        font.setPixelSize(30)
        expected.setFont(font)
        pen = expected.pen()
        pen.setWidth(1)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        expected.setPen(pen)
        padding = 3
        background_colour = QColor('burlywood')
        text_width = CluePainter.find_text_width('dolores sit amet.', expected)
        text_width += 2 * padding
        text_height = CluePainter.find_text_height('X\nX', expected)
        text_rect = QRectF(10, 10,
                           text_width, text_height + 2 * padding)
        draw_gradient_rect(expected,
                           background_colour,
                           text_rect.x(), text_rect.y(),
                           text_rect.width(), text_rect.height(),
                           padding)

        expected.setRenderHint(QPainter.TextAntialiasing, False)
        expected.setRenderHint(QPainter.Antialiasing, False)
        expected.drawText(QRectF(10+padding, 10+padding, 300-2*padding, 100),
                          0,
                          'Lorem ipsum\ndolores sit amet.')

        actual.setFont(font)

        rect = QRectF(10, 10, 300, 100)
        CluePainter.draw_text(rect,
                              'Lorem ipsum\ndolores sit amet.',
                              actual,
                              background=background_colour,
                              is_gradient=True)


# noinspection DuplicatedCode
def test_draw_text_centred(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(400, 190) as (actual, expected):
        expected.fillRect(expected.window(), 'ivory')
        actual.fillRect(actual.window(), 'ivory')

        font = expected.font()
        font.setPixelSize(40)
        expected.setFont(font)

        expected.drawText(QRectF(0, 50, 400, 100),
                          int(Qt.AlignmentFlag.AlignHCenter),
                          'Lorem ipsum\ndolores sit amet.')

        actual.setFont(font)

        rect = QRectF(0, 50, 400, 100)
        CluePainter.draw_text(rect, 'Lorem ipsum', actual, is_centred=True)
        CluePainter.draw_text(rect, 'dolores sit amet.', actual, is_centred=True)


# noinspection DuplicatedCode
def test_draw_text_dry_run(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(740, 190) as (actual, expected):
        expected.fillRect(expected.window(), 'ivory')
        actual.fillRect(actual.window(), 'ivory')

        font = expected.font()
        font.setPixelSize(40)
        expected.setFont(font)

        expected.drawText(QRectF(50, 50, 400, 100),
                          0,
                          'Lorem ipsum\ndolores sit amet.')

        actual.setFont(font)

        rect1 = QRectF(50, 50, 400, 100)
        rect2 = QRectF(rect1)
        CluePainter.draw_text(rect1, 'Lorem ipsum', actual, is_dry_run=True)
        CluePainter.draw_text(rect2, 'Lorem ipsum', actual)
        CluePainter.draw_text(rect1, 'dolores sit amet.', actual)
        CluePainter.draw_text(rect2, 'consectetur', actual, is_dry_run=True)


# noinspection DuplicatedCode
def test_draw_clues(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()
    puzzle.down_clues[1].text_with_reference = "Run between 1 Across"

    margin = 10
    with pixmap_differ.create_painters(740, 190):
        pixmap_differ.radius = 5
        pixmap_differ.tolerance = 30
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter
        font = QFont('NotoSansCJK')
        font.setPixelSize(20)
        expected.setFont(font)
        bounds1 = QRectF(10, 10, 300, 100)
        number_width = CluePainter.find_text_width('1.', expected)
        padded_width = CluePainter.find_text_width('1. ', expected)
        num_rect = QRectF(bounds1)
        num_rect.setWidth(number_width)
        bounds1.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(num_rect, '1.\n3.', expected)
        CluePainter.draw_text(bounds1,
                              'Part of a sentence\nOne at a time',
                              expected)

        actual.setFont(font)
        bounds = QRectF(10, 10, 300, 100)
        clue_painter = CluePainter(puzzle, font_size=20, margin=margin)
        clue_painter.draw_clues(actual, puzzle.across_clues, bounds)


# noinspection DuplicatedCode
def test_draw_page(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()
    puzzle.down_clues[1].text_with_reference = "Run between 1 Across"

    width = 740
    height = 190
    margin = 10
    with pixmap_differ.create_painters(width, height):
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter
        font = QFont('NotoSansCJK')
        font.setPixelSize(40)
        expected.setFont(font)
        pen = expected.pen()
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        expected.setPen(pen)
        header_rect = QRectF(margin, margin, width-2*margin, height-2*margin)
        CluePainter.draw_text(header_rect,
                              'Basic Puzzle',
                              expected,
                              is_centred=True)
        font.setPixelSize(20)
        expected.setFont(font)
        CluePainter.draw_text(header_rect,
                              'Clue numbers are shuffled: 1 Across might not '
                              'be the top left. 3 pieces.',
                              expected)
        line_height = CluePainter.find_text_height('X', expected)
        expected.drawLine(margin, round(header_rect.top() + line_height/2),
                          width-margin, round(header_rect.top() + line_height/2))
        header_rect.adjust(0, line_height, 0, 0)
        left_rect = QRectF(header_rect)
        right_rect = QRectF(header_rect)
        left_rect.setRight(width / 2 - margin)
        right_rect.setLeft(width / 2)
        CluePainter.draw_text(left_rect, 'Across', expected, is_bold=True)
        CluePainter.draw_text(right_rect, 'Down', expected, is_bold=True)

        number_width = CluePainter.find_text_width('1.', expected)
        padded_width = CluePainter.find_text_width('1. ', expected)
        left_num_rect = QRectF(left_rect)
        left_num_rect.setRight(left_num_rect.left() + number_width)
        left_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(left_num_rect, '1.\n3.', expected)
        CluePainter.draw_text(left_rect,
                              'Part of a sentence\nOne at a time',
                              expected)
        right_num_rect = QRectF(right_rect)
        right_num_rect.setWidth(number_width)
        right_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(right_num_rect, '1.\n2.', expected)
        CluePainter.draw_text(right_rect,
                              'Sour grapes\nRun between 1 Across',
                              expected)

        clue_painter = CluePainter(puzzle, font_size=20, margin=margin)
        clue_painter.draw_page(actual)

    assert clue_painter.is_finished


# noinspection DuplicatedCode
def test_draw_page_with_background(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()
    puzzle.down_clues[1].text_with_reference = "Run between 1 Across"
    puzzle_set = PuzzleSet(puzzle)

    width = 740
    height = 190
    margin = 10
    with pixmap_differ.create_painters(width, height):
        bg_tile = puzzle_set.create_background_tile(20, puzzle.face_colour)
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter
        font = QFont('NotoSansCJK')
        puzzle_font = QFont('Courier')
        puzzle_font.setPixelSize(40)
        expected.setFont(puzzle_font)
        header_rect = QRectF(margin, margin,
                             width-2*margin, height-2*margin)
        header_rect2 = QRectF(header_rect)
        CluePainter.draw_text(header_rect,
                              'Basic Puzzle',
                              expected,
                              is_dry_run=True,
                              background=puzzle.face_colour)
        bg_rect = QRectF(0, 0, expected.window().width(), header_rect.top())
        draw_rotated_tiles(bg_tile, expected, 20, bounds=bg_rect)

        pen = expected.pen()
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        expected.setPen(pen)
        expected.drawRect(bg_rect)
        CluePainter.draw_text(header_rect2,
                              'Basic Puzzle',
                              expected,
                              is_centred=True,
                              background=puzzle.face_colour,
                              is_gradient=True)
        font.setPixelSize(20)
        expected.setFont(font)
        CluePainter.draw_text(header_rect,
                              'Clue numbers are shuffled: 1 Across might not '
                              'be the top left. 3 pieces.',
                              expected)
        line_height = CluePainter.find_text_height('X', expected)
        expected.drawLine(margin, round(header_rect.top() + line_height/2),
                          width-margin, round(header_rect.top() + line_height/2))
        header_rect.adjust(0, line_height, 0, 0)
        left_rect = QRectF(header_rect)
        right_rect = QRectF(header_rect)
        left_rect.setRight(width / 2 - margin)
        right_rect.setLeft(width / 2)
        CluePainter.draw_text(left_rect, 'Across', expected, is_bold=True)

        number_width = CluePainter.find_text_width('1.', expected)
        padded_width = CluePainter.find_text_width('1. ', expected)
        left_num_rect = QRectF(left_rect)
        left_num_rect.setRight(left_num_rect.left() + number_width)
        left_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(left_num_rect, '1.', expected)
        CluePainter.draw_text(left_rect,
                              'Part of a sentence',
                              expected)
        right_num_rect = QRectF(right_rect)
        right_num_rect.setWidth(number_width)
        right_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(right_num_rect, '3.', expected)
        CluePainter.draw_text(right_rect,
                              'One at a time',
                              expected)

        puzzle.font = puzzle_font
        clue_painter = CluePainter(puzzle,
                                   font_size=20,
                                   margin=margin,
                                   background=puzzle.face_colour,
                                   background_tile=bg_tile)
        clue_painter.draw_page(actual)


# noinspection DuplicatedCode
def test_draw_clues_wrapped(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()

    puzzle.across_clues[0].text = 'Part of an extremely long, run-on sentence'
    width = 740
    height = 190
    margin = 10
    with pixmap_differ.create_painters(width, height):
        pixmap_differ.radius = 5
        pixmap_differ.tolerance = 30
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter
        font = QFont('NotoSansCJK')
        font.setPixelSize(20)
        title_font = QFont(font)
        title_font.setPixelSize(40)
        puzzle2 = parse_basic_puzzle()
        header_rect = QRectF(margin, margin,
                             width - 2*margin, height - 2*margin)
        clue_painter1 = CluePainter(puzzle2, font_size=20, margin=margin)
        clue_painter1.draw_header(title_font, font, header_rect, expected)
        across_rect = QRectF(header_rect)
        across_rect.setWidth(across_rect.width()/2)
        down_rect = across_rect.translated(across_rect.width(), 0)
        CluePainter.draw_text(across_rect, 'Across', expected, is_bold=True)
        number_width = CluePainter.find_text_width('1.', expected)
        padded_width = CluePainter.find_text_width('1. ', expected)
        num_rect = QRectF(across_rect)
        num_rect.setWidth(number_width)
        across_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(num_rect, '1.', expected, is_aligned_right=True)
        CluePainter.draw_text(across_rect,
                              'Part of an extremely long, run-on\nsentence',
                              expected)

        num_rect = QRectF(down_rect)
        num_rect.setWidth(number_width)
        down_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(num_rect,
                              '3.',
                              expected,
                              is_aligned_right=True)
        CluePainter.draw_text(down_rect,
                              'One at a time',
                              expected)
        down_rect.setLeft(num_rect.left())
        CluePainter.draw_text(down_rect, 'Down', expected, is_bold=True)
        down_rect.adjust(padded_width, 0, 0, 0)
        num_rect.setTop(down_rect.top())
        CluePainter.draw_text(num_rect,
                              '1.',
                              expected,
                              is_aligned_right=True)
        CluePainter.draw_text(down_rect, 'Sour grapes', expected)

        clue_painter2 = CluePainter(puzzle, font_size=20, margin=margin)
        clue_painter2.draw_page(actual)

    assert not clue_painter2.is_finished


# noinspection DuplicatedCode
def test_draw_clues_next_page(pixmap_differ: PixmapDiffer):
    puzzle1 = parse_basic_puzzle()
    puzzle1.across_clues[0].text = 'Part of an extremely long, run-on sentence'
    puzzle2 = parse_basic_puzzle()
    puzzle2.title = 'Next Puzzle'

    width = 740
    height = 190
    margin = 10
    align_right = int(Qt.AlignmentFlag.AlignRight)
    with pixmap_differ.create_painters(width, height):
        pixmap_differ.radius = 5
        pixmap_differ.tolerance = 30
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter
        font = QFont('NotoSansCJK')
        font.setPixelSize(20)
        expected.setFont(font)
        number_width = CluePainter.find_text_width('1.', expected)
        padded_width = CluePainter.find_text_width('1. ', expected)
        expected.drawText(margin, margin,
                          number_width, height,
                          align_right,
                          '2.')
        expected.drawText(margin+padded_width, margin,
                          width, height,
                          0,
                          'Run between words')

        clue_painter = CluePainter(puzzle1,
                                   puzzle2,
                                   font_size=20,
                                   margin=margin)
        clue_painter.draw_page(actual)
        actual.eraseRect(actual.window())
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
    with pixmap_differ.create_painters(width, height):
        pixmap_differ.radius = 6
        pixmap_differ.tolerance = 30
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter
        font = QFont('NotoSansCJK')
        font.setPixelSize(40)
        expected.setFont(font)
        header_rect = QRectF(margin, margin, width-2*margin, height-2*margin)
        CluePainter.draw_text(header_rect,
                              'Basic Puzzle',
                              expected,
                              is_centred=True)
        font.setPixelSize(20)
        expected.setFont(font)
        CluePainter.draw_text(header_rect,
                              'Clue numbers are shuffled: 1 Across might not '
                              'be the top left. 3 pieces.',
                              expected)
        line_height = CluePainter.find_text_height('X', expected)
        expected.drawLine(margin, round(header_rect.top() + line_height/2),
                          width-margin, round(header_rect.top() + line_height/2))
        header_rect.adjust(0, line_height, 0, 0)
        left_rect = QRectF(header_rect)
        right_rect = QRectF(header_rect)
        left_rect.setRight(width / 2 - margin)
        right_rect.setLeft(width / 2)
        CluePainter.draw_text(left_rect, 'Across', expected, is_bold=True)
        CluePainter.draw_text(right_rect, 'Down', expected, is_bold=True)

        number_width = CluePainter.find_text_width('1♡.', expected)
        padded_width = CluePainter.find_text_width('1♡. ', expected)
        left_num_rect = QRectF(left_rect)
        left_num_rect.setRight(left_num_rect.left() + number_width)
        left_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(left_num_rect, '1♢.\n3♡.', expected)
        CluePainter.draw_text(left_rect,
                              'Part of a sentence\nOne at a time',
                              expected)
        right_num_rect = QRectF(right_rect)
        right_num_rect.setWidth(number_width)
        right_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(right_num_rect, '1♣.\n2♠.', expected)
        CluePainter.draw_text(right_rect,
                              'Sour grapes\nRun between words',
                              expected)

        clue_painter = CluePainter(puzzle, font_size=20, margin=margin)
        clue_painter.draw_page(actual)


# noinspection DuplicatedCode
def test_draw_clues_face_colour(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()
    puzzle_set = PuzzleSet(puzzle)
    puzzle.face_colour = QColor.fromHsv(120, 60, 255)

    width = 740
    height = 190
    margin = 10
    with pixmap_differ.create_painters(width, height):
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter
        bg_tile = puzzle_set.create_background_tile(20, QColor('burlywood'))
        font = QFont('NotoSansCJK')
        font.setPixelSize(20)
        title_font = QFont(font)
        title_font.setPixelSize(40)
        puzzle2 = parse_basic_puzzle()
        header_rect = QRectF(margin, margin,
                             width - 2*margin, height - 2*margin)
        clue_painter1 = CluePainter(puzzle2, font_size=20, margin=margin)
        clue_painter1.background = puzzle.face_colour
        clue_painter1.background_tile = bg_tile
        clue_painter1.draw_header(title_font, font, header_rect, expected)
        across_rect = QRectF(header_rect)
        across_rect.setWidth(across_rect.width()/2)
        down_rect = across_rect.translated(across_rect.width(), 0)
        CluePainter.draw_text(across_rect, 'Across', expected, is_bold=True)
        number_width = CluePainter.find_text_width('1.', expected)
        space_width = CluePainter.find_text_width(' ', expected)
        padded_width = number_width + space_width
        num_rect = QRectF(across_rect)
        num_rect.setWidth(number_width)
        across_rect.adjust(padded_width, 0, 0, 0)

        num_rect2 = QRectF(down_rect)
        num_rect2.setWidth(number_width)
        down_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(across_rect,
                              'Part of a sentence',
                              expected)
        CluePainter.draw_text(num_rect,
                              '1.',
                              expected,
                              is_aligned_right=True)
        CluePainter.draw_text(num_rect2,
                              '3.',
                              expected,
                              is_aligned_right=True)
        CluePainter.draw_text(down_rect,
                              'One at a time',
                              expected)

        clue_painter = CluePainter(puzzle, font_size=20, margin=margin)
        clue_painter.background_tile = bg_tile
        clue_painter.background = puzzle.face_colour
        clue_painter.draw_page(actual)


# noinspection DuplicatedCode
def test_draw_clues_long_title(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()
    puzzle.title = 'Long Title That Will Not Fit (1000x2000)'

    width = 740
    height = 250
    margin = 10
    with pixmap_differ.create_painters(width, height):
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter
        font = QFont('NotoSansCJK')
        font.setPixelSize(40)
        expected.setFont(font)
        header_rect = QRectF(margin, margin, width-2*margin, height-2*margin)
        CluePainter.draw_text(header_rect,
                              'Long Title That Will Not Fit\n(1000x2000)',
                              expected,
                              is_centred=True)
        font.setPixelSize(20)
        expected.setFont(font)
        CluePainter.draw_text(header_rect,
                              'Clue numbers are shuffled: 1 Across might not '
                              'be the top left. 3 pieces.',
                              expected)
        line_height = CluePainter.find_text_height('X', expected)
        pen = expected.pen()
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        expected.setPen(pen)
        expected.drawLine(margin, round(header_rect.top() + line_height/2),
                          width-margin, round(header_rect.top() + line_height/2))
        header_rect.adjust(0, line_height, 0, 0)
        left_rect = QRectF(header_rect)
        right_rect = QRectF(header_rect)
        left_rect.setRight(width / 2 - margin)
        right_rect.setLeft(width / 2)
        CluePainter.draw_text(left_rect, 'Across', expected, is_bold=True)
        CluePainter.draw_text(right_rect, 'Down', expected, is_bold=True)

        number_width = CluePainter.find_text_width('1.', expected)
        padded_width = CluePainter.find_text_width('1. ', expected)
        left_num_rect = QRectF(left_rect)
        left_num_rect.setRight(left_num_rect.left() + number_width)
        left_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(left_num_rect, '1.\n3.', expected)
        CluePainter.draw_text(left_rect,
                              'Part of a sentence\nOne at a time',
                              expected)
        right_num_rect = QRectF(right_rect)
        right_num_rect.setWidth(number_width)
        right_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(right_num_rect, '1.\n2.', expected)
        CluePainter.draw_text(right_rect,
                              'Sour grapes\nRun between words',
                              expected)

        clue_painter = CluePainter(puzzle, font_size=20, margin=margin)
        clue_painter.draw_page(actual)


# noinspection DuplicatedCode
def test_draw_clues_intro(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()

    width = 740
    height = 190
    margin = 10
    with pixmap_differ.create_painters(width, height):
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter
        font = QFont('NotoSansCJK')
        font.setPixelSize(20)
        expected.setFont(font)
        title_font = QFont(font)
        title_font.setPixelSize(40)
        puzzle2 = parse_basic_puzzle()
        header_rect = QRectF(margin, margin,
                             width - 2*margin, height - 2*margin)
        CluePainter.draw_text(header_rect, 'Introduction...', expected)
        clue_painter1 = CluePainter(puzzle2, font_size=20, margin=margin)
        clue_painter1.draw_header(title_font, font, header_rect, expected)
        across_rect = QRectF(header_rect)
        across_rect.setWidth(across_rect.width()/2)
        down_rect = across_rect.translated(across_rect.width(), 0)
        CluePainter.draw_text(across_rect, 'Across', expected, is_bold=True)
        number_width = CluePainter.find_text_width('1.', expected)
        padded_width = CluePainter.find_text_width('1. ', expected)
        num_rect = QRectF(across_rect)
        num_rect.setWidth(number_width)
        across_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(num_rect, '1.', expected, is_aligned_right=True)
        CluePainter.draw_text(across_rect, 'Part of a sentence', expected)
        num_rect = QRectF(down_rect)
        num_rect.setWidth(number_width)
        down_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(num_rect,
                              '3.',
                              expected,
                              is_aligned_right=True)
        CluePainter.draw_text(down_rect, 'One at a time', expected)

        clue_painter = CluePainter(puzzle,
                                   font_size=20,
                                   margin=margin,
                                   intro_text='Introduction...')
        clue_painter.draw_page(actual)


# noinspection DuplicatedCode
def test_draw_clues_intro_and_tile(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()
    puzzle_set = PuzzleSet(puzzle)

    width = 740
    height = 200
    margin = 10
    with pixmap_differ.create_painters(width, height):
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter
        bg_tile = puzzle_set.create_background_tile(20, puzzle.face_colour)
        pen = expected.pen()
        pen.setWidth(2)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        expected.setPen(pen)
        font = QFont('NotoSansCJK')
        font.setPixelSize(20)
        expected.setFont(font)
        title_font = QFont(font)
        title_font.setPixelSize(40)
        header_rect = QRectF(margin, margin,
                             width - 2*margin, height - 2*margin)
        CluePainter.draw_text(header_rect, 'Introduction...', expected)
        temp_rect = QRectF(header_rect)
        expected.setFont(title_font)
        CluePainter.draw_text(temp_rect,
                              puzzle.title,
                              expected,
                              background=puzzle.face_colour,
                              is_dry_run=True)
        bg_rect = QRectF(0, header_rect.top(),
                         width, temp_rect.top()-header_rect.top())
        draw_rotated_tiles(bg_tile, expected, 20, bounds=bg_rect)
        expected.drawRect(bg_rect)

        CluePainter.draw_text(header_rect,
                              puzzle.title,
                              expected,
                              is_centred=True,
                              background=puzzle.face_colour,
                              is_gradient=True)
        expected.setFont(font)
        CluePainter.draw_text(header_rect,
                              'Clue numbers are shuffled: 1 Across might not '
                              'be the top left. 3 pieces.',
                              expected)
        line_height = CluePainter.find_text_height('X', expected)
        y = header_rect.top() + round(line_height / 2)
        expected.drawLine(10, y, width-10, y)
        header_rect.adjust(0, line_height, 0, 0)
        across_rect = QRectF(header_rect)
        across_rect.setWidth(across_rect.width()/2)
        down_rect = across_rect.translated(across_rect.width(), 0)
        CluePainter.draw_text(across_rect, 'Across', expected, is_bold=True)
        number_width = CluePainter.find_text_width('1.', expected)
        padded_width = CluePainter.find_text_width('1. ', expected)
        num_rect = QRectF(across_rect)
        num_rect.setWidth(number_width)
        across_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(num_rect, '1.', expected, is_aligned_right=True)
        CluePainter.draw_text(across_rect, 'Part of a sentence', expected)
        num_rect = QRectF(down_rect)
        num_rect.setWidth(number_width)
        down_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(num_rect,
                              '3.',
                              expected,
                              is_aligned_right=True)
        CluePainter.draw_text(down_rect, 'One at a time', expected)

        clue_painter = CluePainter(puzzle,
                                   font_size=20,
                                   margin=margin,
                                   intro_text='Introduction...')
        clue_painter.background_tile = bg_tile
        clue_painter.background = puzzle.face_colour
        clue_painter.draw_page(actual)


# noinspection DuplicatedCode
def test_draw_clues_footer(pixmap_differ: PixmapDiffer):
    puzzle = parse_basic_puzzle()

    width = 740
    height = 190
    margin = 10
    with pixmap_differ.create_painters(width, height):
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter
        font = QFont('NotoSansCJK')
        font.setPixelSize(20)
        expected.setFont(font)
        title_font = QFont(font)
        title_font.setPixelSize(40)
        puzzle2 = parse_basic_puzzle()
        header_rect = QRectF(margin, margin,
                             width - 2*margin, height - 2*margin)
        clue_painter1 = CluePainter(puzzle2, font_size=20, margin=margin)
        clue_painter1.draw_header(title_font, font, header_rect, expected)
        across_rect = QRectF(header_rect)
        across_rect.setWidth(across_rect.width()/2)
        down_rect = across_rect.translated(across_rect.width(), 0)
        CluePainter.draw_text(across_rect, 'Across', expected, is_bold=True)
        number_width = CluePainter.find_text_width('1.', expected)
        padded_width = CluePainter.find_text_width('1. ', expected)
        num_rect = QRectF(across_rect)
        num_rect.setWidth(number_width)
        across_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(num_rect, '1.', expected, is_aligned_right=True)
        CluePainter.draw_text(across_rect, 'Part of a sentence', expected)
        num_rect = QRectF(down_rect)
        num_rect.setWidth(number_width)
        down_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(num_rect,
                              '3.',
                              expected,
                              is_aligned_right=True)
        CluePainter.draw_text(down_rect, 'One at a time', expected)
        footer = 'https://example.com'
        footer_height = CluePainter.find_text_height(footer, expected)
        CluePainter.draw_text(QRectF(0, height-margin-footer_height,
                                     width, footer_height),
                              footer,
                              expected,
                              is_centred=True)

        clue_painter = CluePainter(puzzle,
                                   font_size=20,
                                   margin=margin,
                                   footer_text='https://example.com')
        clue_painter.draw_page(actual)
