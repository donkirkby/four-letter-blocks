from textwrap import dedent

from PySide6.QtCore import QPoint
from PySide6.QtGui import QPen, Qt, QColor, QPainter, QPainterPath, QFont
from colorspacious import cspace_convert

from four_letter_blocks.grid import Grid
from four_letter_blocks.block import Block
from four_letter_blocks.square import Square, draw_gradient_rect
from tests.test_square import PixmapDiffer


def create_basic_block():
    # (x, y) == (0, 50)
    # ABC
    # D
    square1 = Square('A')
    square2 = Square('B')
    square3 = Square('C')
    square4 = Square('D')
    square2.y = 1
    square3.x = 1
    square4.x = 2
    block = Block(square1, square2, square3, square4)
    for square in block.squares:
        square.size = 100
        square.x *= 100
        square.y = square.y*100 + 50
    return block


def test_repr():
    block = Block(Square('W'), Square('O', 12))

    assert repr(block) == "Block(Square('W'), Square('O', 12))"


def test_parse():
    grid_text = """\
WORD
I##A
N##S
EACH
"""
    block_text = """\
AABB
A##B
A##B
CCCC
"""
    grid = Grid(grid_text)

    blocks = Block.parse(block_text, grid)

    assert len(blocks) == 3
    assert blocks[0].squares[1].letter == 'O'
    assert blocks[0].squares[1].x == 1
    assert blocks[0].squares[1].y == 0


def test_parse_sorted_by_marker():
    grid_text = """\
WORD
I##A
N##S
EACH
"""
    block_text = """\
XXBB
X##B
X##B
AAAA
"""
    grid = Grid(grid_text)

    blocks = Block.parse(block_text, grid)

    assert len(blocks) == 3
    assert blocks[2].squares[1].letter == 'O'
    assert blocks[2].squares[1].x == 1
    assert blocks[2].squares[1].y == 0


def test_parse_mismatch():
    grid_text = """\
WORD
I##A
N##S
EACH
"""
    block_text = """\
AAB#
A#BB
A##B
CCCC
"""
    grid = Grid(grid_text)

    blocks = Block.parse(block_text, grid)

    assert len(blocks) == 4
    assert blocks[1].marker == 'B'
    assert len(blocks[1].squares) == 3  # One of them didn't match with a square.
    assert blocks[3].marker == 'unused'
    assert len(blocks[3].squares) == 1


def test_parse_blocks_bigger_than_grid():
    grid_text = """\
WORD
I##A
N##S
EACH
"""
    block_text = """\
AABBDE
A##BDE
A##BDE
CCCCDE
"""
    grid = Grid(grid_text)

    blocks = Block.parse(block_text, grid)

    assert len(blocks) == 3
    assert blocks[1].marker == 'B'


def test_parse_blocks_smaller_than_grid():
    grid_text = """\
WORD
I##A
N##S
EACH
"""
    block_text = """\
AA??
A##?
A##?
"""
    grid = Grid(grid_text)

    blocks = Block.parse(block_text, grid)

    assert len(blocks) == 2
    assert blocks[1].marker == Block.UNUSED
    assert len(blocks[1].squares) == 8


def test_move():
    block = create_basic_block()
    square1, square2, square3, square4 = block.squares

    assert block.x == 0
    assert block.y == 50
    assert block.width == 300
    assert block.height == 200

    block.x = 300

    assert square1.x == 300
    assert square3.x == 400

    block.y = 100

    assert square1.y == 100
    assert square2.y == 200


def test_shape():
    grid_text = dedent("""\
        ABCDEFGHI
        RQPONMLKJ
        STUVWXY#Z
        #FEDCB##A""")
    block_text = dedent("""\
        AABBBCCEG
        AABDDCEEG
        HHDDFCE#G
        #HHFFF##G""")
    grid = Grid(grid_text)

    blocks = dict(zip('ABCDEFGH', Block.parse(block_text, grid)))
    assert blocks['A'].shape == 'O'
    assert blocks['A'].shape_rotation == 0
    assert blocks['B'].shape == 'L'
    assert blocks['B'].shape_rotation == 3
    assert blocks['C'].shape == 'J'
    assert blocks['D'].shape == 'S'
    assert blocks['E'].shape == 'Z'
    assert blocks['E'].shape_rotation == 1
    assert blocks['F'].shape == 'T'
    assert blocks['G'].shape == 'I'
    assert blocks['H'].shape == 'Z'
    assert blocks['H'].shape_rotation == 0


# noinspection DuplicatedCode
def test_draw(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(310, 260) as (actual, expected):
        block = create_basic_block()
        block.border_colour = 'blue'
        block.divider_colour = 'magenta'

        for square in block.squares:
            square.draw(expected)

        pen = QPen('magenta')
        pen.setWidth(3)
        expected.setPen(pen)
        expected.drawLine(0, 150, 100, 150)
        expected.drawLine(100, 50, 100, 150)
        expected.drawLine(200, 50, 200, 150)

        pen = QPen('blue')
        pen.setWidth(3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        expected.setPen(pen)
        expected.drawLine(0, 50, 300, 50)
        expected.drawLine(100, 150, 300, 150)
        expected.drawLine(0, 250, 100, 250)
        expected.drawLine(0, 50, 0, 250)
        expected.drawLine(100, 150, 100, 250)
        expected.drawLine(300, 50, 300, 150)

        block.draw(actual)


# noinspection DuplicatedCode
def test_draw_font(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(310, 260) as (actual, expected):
        font = QFont('Courier')
        block = create_basic_block()
        block.border_colour = 'blue'
        block.divider_colour = 'magenta'

        expected.setFont(font)
        for square in block.squares:
            square.draw(expected)

        pen = QPen('magenta')
        pen.setWidth(3)
        expected.setPen(pen)
        expected.drawLine(0, 150, 100, 150)
        expected.drawLine(100, 50, 100, 150)
        expected.drawLine(200, 50, 200, 150)

        pen = QPen('blue')
        pen.setWidth(3)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        expected.setPen(pen)
        expected.drawLine(0, 50, 300, 50)
        expected.drawLine(100, 150, 300, 150)
        expected.drawLine(0, 250, 100, 250)
        expected.drawLine(0, 50, 0, 250)
        expected.drawLine(100, 150, 100, 250)
        expected.drawLine(300, 50, 300, 150)

        block.font = font
        block.draw(actual)


# noinspection DuplicatedCode
def test_draw_with_tabs(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(400, 260) as (actual, expected):
        block = create_basic_block()
        block.tab_count = 1

        for square in block.squares:
            square.draw(expected)

        pen = QPen()
        pen.setWidth(3)
        expected.setPen(pen)

        expected.drawLine(25, 150, 75, 150)
        expected.drawLine(100, 75, 100, 125)
        expected.drawLine(200, 75, 200, 125)

        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        expected.setPen(pen)
        path = QPainterPath(QPoint(-50, 0))
        path.lineTo(-37.5, 0)
        path.cubicTo(-25, 0, -20, -12.5, -12.5, -12.5)
        path.cubicTo(-8, -12.5, -7, -7, -8, -5)
        path.cubicTo(-9, -3, -14, 5, -12, 7)
        path.cubicTo(-10, 9, -10, 12.5, 0, 12.5)
        path.cubicTo(10, 12.5, 10, 9, 12, 7)
        path.cubicTo(14, 5, 9, -3, 8, -5)
        path.cubicTo(7, -7, 8, -12.5, 12.5, -12.5)
        path.cubicTo(20, -12.5, 25, 0, 37.5, 0)
        path.lineTo(50, 0)
        path.translate(50, 50)
        expected.drawPath(path)
        path.translate(0, 200)
        expected.drawPath(path)
        path.translate(100, -200)
        expected.drawPath(path)
        path.translate(0, 100)
        expected.drawPath(path)
        path.translate(100, -100)
        expected.drawPath(path)
        path.translate(0, 100)
        expected.drawPath(path)
        path.translate(0, -100)
        expected.rotate(-90)
        path.translate(-350, 250)
        expected.drawPath(path)
        path.translate(0, -300)
        expected.drawPath(path)
        path.translate(-100, 0)
        expected.drawPath(path)
        path.translate(0, 100)
        expected.drawPath(path)
        expected.rotate(90)

        block.draw(actual)


# noinspection DuplicatedCode
def test_double_tabs(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(400, 260) as (actual, expected):
        block = create_basic_block()
        block.squares[0].number = 23
        block.squares[0].suit = 'H'
        block.tab_count = 2

        for square in block.squares:
            square.draw(expected, is_packed=True)

        pen = QPen()
        pen.setWidth(3)
        expected.setPen(pen)
        expected.drawLine(25, 150, 75, 150)
        expected.drawLine(100, 75, 100, 125)
        expected.drawLine(200, 75, 200, 125)

        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        expected.setPen(pen)
        path = QPainterPath(QPoint(-50, 0))
        path.lineTo(-15, 0)
        path.arcTo(-22, -13.3, 13.3, 13.3, -90, 66)
        path.arcTo(-10, -10, 20, 20, 156.4, -66.4)
        path.arcTo(-5, -10, 10, 10, 90, -180)
        path.arcTo(-5, 0, 10, 10, 90, 180)
        path.arcTo(-10, -10, 20, 20, 270, 66.4)
        path.arcTo(8.6, 0, 13.3, 13.3, 156, -66)
        path.lineTo(50, 0)
        path.translate(50, 50)
        expected.drawPath(path)
        path.translate(0, 200)
        expected.drawPath(path)
        path.translate(100, -200)
        expected.drawPath(path)
        path.translate(0, 100)
        expected.drawPath(path)
        path.translate(100, -100)
        expected.drawPath(path)
        path.translate(0, 100)
        expected.drawPath(path)
        path.translate(0, -100)
        expected.rotate(-90)
        path.translate(-350, 250)
        expected.drawPath(path)
        path.translate(0, -300)
        expected.drawPath(path)
        path.translate(-100, 0)
        expected.drawPath(path)
        path.translate(0, 100)
        expected.drawPath(path)
        expected.rotate(90)

        block.draw(actual, is_packed=True)
        block.draw_outline(actual)


# noinspection DuplicatedCode
def test_double_tabs_short(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(400, 260) as (actual, expected):
        block = create_basic_block()
        block.tab_count = 2

        pen = QPen()
        pen.setWidth(3)
        expected.setPen(pen)

        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        expected.setPen(pen)
        path = QPainterPath(QPoint(-30, 0))
        path.lineTo(-15, 0)
        path.arcTo(-22, -13.3, 13.3, 13.3, -90, 66)
        path.arcTo(-10, -10, 20, 20, 156.4, -66.4)
        path.arcTo(-5, -10, 10, 10, 90, -180)
        path.arcTo(-5, 0, 10, 10, 90, 180)
        path.arcTo(-10, -10, 20, 20, 270, 66.4)
        path.arcTo(8.6, 0, 13.3, 13.3, 156, -66)
        path.lineTo(30, 0)
        path.translate(50, 50)
        expected.drawPath(path)

        actual.setPen(pen)
        block.draw_nicked_line(actual, 0, 20, 50, 80, 50)


# noinspection DuplicatedCode
def test_double_tabs_too_short(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(400, 260) as (actual, expected):
        block = create_basic_block()  # square size is 100
        block.tab_count = 2

        pen = QPen()
        pen.setWidth(3)
        expected.setPen(pen)

        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        expected.setPen(pen)
        expected.drawLine(26, 50, 74, 50)

        actual.setPen(pen)
        block.draw_nicked_line(actual, 0, 26, 50, 74, 50)


# noinspection DuplicatedCode
def test_draw_nicked_line(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(400, 260) as (actual, expected):
        block = create_basic_block()  # square size is 100

        pen = QPen()
        pen.setWidth(3)
        expected.setPen(pen)

        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        expected.setPen(pen)
        expected.drawLine(20, 50, 60, 50)
        expected.drawLine(70, 50, 150, 50)
        expected.drawLine(160, 50, 200, 50)

        actual.setPen(pen)
        block.draw_nicked_line(actual, 5, 20, 50, 200, 50)


# noinspection DuplicatedCode
def test_draw_packed(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(310, 260) as (actual, expected):
        block = create_basic_block()
        block.border_colour = 'blue'
        block.divider_colour = 'magenta'

        for square in block.squares:
            square.draw(expected, is_packed=True)

        pen = QPen(QColor('magenta'), 3)
        expected.setPen(pen)
        expected.drawLine(25, 150, 75, 150)
        expected.drawLine(100, 75, 100, 125)
        expected.drawLine(200, 75, 200, 125)

        block.draw(actual, is_packed=True)


# noinspection DuplicatedCode
def test_draw_packed_with_rounding(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(310, 260) as (actual, expected):
        block = create_basic_block()
        block.border_colour = 'blue'
        block.divider_colour = 'magenta'
        block.squares[1].y += 1
        block.squares[3].x += 1

        for square in block.squares:
            square.draw(expected, is_packed=True)

        pen = QPen(QColor('magenta'), 3)
        expected.setPen(pen)
        expected.drawLine(25, 151, 75, 151)
        expected.drawLine(100, 75, 100, 125)
        expected.drawLine(201, 75, 201, 125)

        block.draw(actual, is_packed=True)


def test_draw_face_colour(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(370, 260) as (actual, expected):
        lightness = 81
        chroma = 20
        bg_hue = 0
        face_hue = 180
        bg_rgb = cspace_convert((lightness, chroma, bg_hue), "JCh", "sRGB255")
        face_rgb = cspace_convert((lightness, chroma, face_hue), "JCh", "sRGB255")
        bg_colour = QColor.fromRgb(*bg_rgb)
        face_colour = QColor.fromRgb(*face_rgb)
        expected.fillRect(expected.window(), bg_colour)

        draw_gradient_rect(expected,
                           face_colour,
                           106.25, 56.25,
                           87.5, 87.5,
                           31.25)
        draw_gradient_rect(expected,
                           face_colour,
                           6.25, 56.25,
                           87.5, 87.5,
                           31.25)
        draw_gradient_rect(expected,
                           face_colour,
                           206.25, 56.25,
                           87.5, 87.5,
                           31.25)
        draw_gradient_rect(expected,
                           face_colour,
                           6.25, 156.25,
                           87.5, 87.5,
                           31.25)

        block = create_basic_block()
        block.squares[0].number = 12
        block.squares[0].suit = 'D'
        block.squares[1].number = 5
        block.squares[1].suit = 'C'
        block.face_colour = QColor.fromHsv(0, 0, 0, 0)
        block.draw(expected, is_packed=True)

        actual.fillRect(actual.window(), bg_colour)
        block.face_colour = face_colour
        block.draw(actual, is_packed=True)


def test_rotate180(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(410, 260) as (actual, expected):
        block1 = create_basic_block()
        block2 = create_basic_block()

        block1.draw(expected)
        expected.rotate(180)
        expected.translate(-400, -300)
        block2.draw(expected)

        block2.x = 100
        block2.set_display(100, 50, rotation=1)

        block1.draw(actual)
        block2.draw(actual)


def test_rotate90(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(510, 260) as (actual, expected):
        block1 = create_basic_block()
        block2 = create_basic_block()

        block1.draw(expected)
        expected.translate(550, 50)
        expected.rotate(90)
        block2.draw(expected)

        block2.x = 100
        block2.set_display(300, 50, rotation=2)

        block1.draw(actual)
        block2.draw(actual)


def test_rotate270(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(510, 260) as (actual, expected):
        block1 = create_basic_block()
        block2 = create_basic_block()

        block1.draw(expected)
        expected.translate(250, 350)
        expected.rotate(270)
        block2.draw(expected)

        block2.x = 100
        block2.set_display(300, 50, rotation=0)

        block1.draw(actual)
        block2.draw(actual)


def test_fractional_position(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(510, 260) as (actual, expected):
        block1 = create_basic_block()
        block1.x = 100

        block1.draw(expected)

        block1.x = 100.2
        block1.draw(actual)


def test_shape_names():
    assert Block.shape_names() == ['I', 'J', 'L', 'O', 'S', 'T', 'Z']
