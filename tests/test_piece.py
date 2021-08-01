from four_letter_blocks.grid import Grid
from four_letter_blocks.piece import Piece
from four_letter_blocks.square import Square
from tests.test_square import PixmapDiffer


def create_basic_piece():
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
    piece = Piece(square1, square2, square3, square4)
    for square in piece.squares:
        square.size = 100
    return piece


def test_repr():
    piece = Piece(Square('W'), Square('O', 12))

    assert repr(piece) == "Piece(Square('W'), Square('O', 12))"


def test_parse():
    grid_text = """\
WORD
I##A
N##S
EACH
"""
    piece_text = """\
AABB
A##B
A##B
CCCC
"""
    grid = Grid(grid_text)

    pieces = Piece.parse(piece_text, grid)

    assert len(pieces) == 3
    assert pieces[0].squares[1].letter == 'O'
    assert pieces[0].squares[1].x == 1
    assert pieces[0].squares[1].y == 0


def test_move():
    piece = create_basic_piece()
    square1, square2, square3, square4 = piece.squares

    assert piece.x == 0
    assert piece.y == 50
    assert piece.width == 300
    assert piece.height == 200

    piece.x = 300

    assert square1.x == 300
    assert square3.x == 400

    piece.y = 100

    assert square1.y == 100
    assert square2.y == 200


def test_draw(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        310, 260,
        'test_piece_draw')

    piece = create_basic_piece()

    for square in piece.squares:
        square.draw(expected)

    piece.draw(actual)

    pixmap_differ.assert_equal()
