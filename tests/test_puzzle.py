from io import StringIO

import pytest

from four_letter_blocks.puzzle import Puzzle
import four_letter_blocks.puzzle
from tests.pixmap_differ import PixmapDiffer


def reverse(a: list):
    a.reverse()


def parse_basic_puzzle():
    source_file = StringIO("""\
WORD
I##A
N##S
EACH

Across
WORD - Part of a sentence
EACH - One at a time

Down
WINE - Sour grapes
DASH - Run between words

AABB
A##B
A##B
CCCC
""")
    puzzle = Puzzle.parse(source_file)
    return puzzle


def test_parse(monkeypatch):
    monkeypatch.setattr(four_letter_blocks.puzzle, 'shuffle', reverse)
    puzzle = parse_basic_puzzle()

    assert puzzle.grid[0, 0].letter == 'W'
    assert puzzle.pieces[0].squares[0].letter == 'E'
    assert puzzle.pieces[0].squares[0].across_word == 'EACH'
    assert puzzle.pieces[0].squares[0].number == 1
    assert puzzle.across_clues[0] == '1. One at a time'


def test_missing_section():
    source_file = StringIO("""\
WORD
I##A
N##S
EACH

Across
WORD - Part of a sentence
EACH - One at a time

Down
WINE - Sour grapes
DASH - Run between words
""")
    with pytest.raises(SystemExit, match='Expected 4 sections, found 3.'):
        Puzzle.parse(source_file)


def test_resize():
    puzzle = parse_basic_puzzle()

    puzzle.square_size = 100

    assert puzzle.grid[1, 0].size == 100
    assert puzzle.grid[1, 0].x == 100
    assert puzzle.grid[0, 2].y == 200
    assert puzzle.pieces[0].squares[0].size == 100


def test_draw_pieces(monkeypatch, pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        180, 180,
        'test_puzzle_draw_pieces')
    monkeypatch.setattr(four_letter_blocks.puzzle, 'shuffle', reverse)

    puzzle1 = parse_basic_puzzle()
    puzzle1.square_size = 20
    piece1, piece2, piece3 = puzzle1.pieces
    piece1.x = 20
    piece1.y = 20
    piece2.x = 110
    piece2.y = 20
    piece3.x = 20
    piece3.y = 90
    piece1.draw(expected)
    piece2.draw(expected)
    piece3.draw(expected)

    puzzle2 = parse_basic_puzzle()
    puzzle2.draw_pieces(actual, square_size=20)

    pixmap_differ.assert_equal()


def test_draw_clues(monkeypatch, pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        400, 180,
        'test_puzzle_draw_clues')
    monkeypatch.setattr(four_letter_blocks.puzzle, 'shuffle', reverse)

    puzzle = parse_basic_puzzle()
    across_clue1, across_clue2 = puzzle.across_clues
    down_clue1, down_clue2 = puzzle.down_clues

    font = expected.font()
    font.setPixelSize(11)
    expected.setFont(font)
    expected.drawText(15, 15, 'Across')
    expected.drawText(15, 30, across_clue1)
    expected.drawText(15, 45, across_clue2)
    expected.drawText(200, 15, 'Down')
    expected.drawText(200, 30, down_clue1)
    expected.drawText(200, 45, down_clue2)

    puzzle.draw_clues(actual, square_size=20)

    pixmap_differ.assert_equal()
