from four_letter_blocks.grid import Grid
from four_letter_blocks.piece import Piece
import four_letter_blocks.piece
from four_letter_blocks.square import Square


def reverse(a: list):
    a.reverse()


def test_repr():
    piece = Piece([Square('W'), Square('O', 12)])

    assert repr(piece) == "Piece([Square('W'), Square('O', 12)])"


def test_parse(monkeypatch):
    monkeypatch.setattr(four_letter_blocks.piece, 'shuffle', reverse)
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
    assert pieces[-1].squares[1].letter == 'O'
    assert pieces[-1].squares[1].x == 1
    assert pieces[-1].squares[1].y == 0
