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
    square1.y = 50
    square2.y = 150
    square3.x = 100
    square3.y = 50
    square4.x = 200
    square4.y = 50
    block = Block(square1, square2, square3, square4)
    for square in block.squares:
        square.size = 100
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


def test_draw(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        310, 260,
        'test_block_draw')

    block = create_basic_block()

    for square in block.squares:
        square.draw(expected)

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

    block.draw(actual, use_text_path=True)

    pixmap_differ.compare()
    assert pixmap_differ.diff_count <= 2500
