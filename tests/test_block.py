from textwrap import dedent

from PySide6.QtGui import QPen, Qt

from four_letter_blocks.grid import Grid
from four_letter_blocks.block import Block
from four_letter_blocks.square import Square
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


def test_draw(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        310, 260,
        'test_block_draw')

    block = create_basic_block()
    block.border_colour = 'blue'
    block.divider_colour = 'magenta'

    for square in block.squares:
        square.draw(expected)

    pen = QPen('magenta')
    expected.setPen(pen)
    expected.drawLine(0, 150, 100, 150)
    expected.drawLine(100, 50, 100, 150)
    expected.drawLine(200, 50, 200, 150)

    pen = QPen('blue')
    pen.setWidth(3)
    pen.setCapStyle(Qt.RoundCap)
    expected.setPen(pen)
    expected.drawLine(0, 50, 300, 50)
    expected.drawLine(100, 150, 300, 150)
    expected.drawLine(0, 250, 100, 250)
    expected.drawLine(0, 50, 0, 250)
    expected.drawLine(100, 150, 100, 250)
    expected.drawLine(300, 50, 300, 150)

    block.draw(actual)

    pixmap_differ.assert_equal()


def test_draw_path(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        310, 260,
        'test_block_draw_path')
    actual.drawText = lambda *args: None
    block = create_basic_block()
    block.squares[0].number = 12
    block.squares[0].suit = 'D'
    block.squares[1].number = 5
    block.squares[1].suit = 'C'
    block.draw(expected)

    block.draw(actual, use_text=False)

    pixmap_differ.compare()
    assert pixmap_differ.diff_count <= 2500


def test_rotate180(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        410, 260,
        'test_block_rotate180')

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

    pixmap_differ.assert_equal()


def test_rotate90(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        510, 260,
        'test_block_rotate90')

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

    pixmap_differ.assert_equal()


def test_rotate270(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        510, 260,
        'test_block_rotate270')

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

    pixmap_differ.assert_equal()
