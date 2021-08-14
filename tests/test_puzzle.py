from io import StringIO

import pytest
from PySide6.QtCore import Qt

from four_letter_blocks.puzzle import Puzzle
import four_letter_blocks.puzzle
from tests.pixmap_differ import PixmapDiffer


def reverse(a: list):
    a.reverse()


def parse_basic_puzzle():
    source_file = StringIO("""\
Basic Puzzle

WORD
I##A
N##S
EACH

WORD - Part of a sentence
EACH - One at a time
WINE - Sour grapes
DASH - Run between words

AABB
A##B
A##B
CCCC
""")
    puzzle = Puzzle.parse(source_file)
    return puzzle


def test_parse():
    puzzle = parse_basic_puzzle()

    assert puzzle.title == 'Basic Puzzle'
    assert puzzle.grid[0, 0].letter == 'W'
    assert puzzle.blocks[2].squares[0].letter == 'E'
    assert puzzle.blocks[2].squares[0].across_word == 'EACH'
    assert puzzle.blocks[2].squares[0].number == 3
    assert puzzle.across_clues[1] == '3. One at a time'
    assert puzzle.all_clues['EACH'] == 'One at a time'


def test_extra_section():
    source_file = StringIO("""\
Puzzle With Extra

WORD
I##A
N##S
EACH

WORD - Part of a sentence
EACH - One at a time
WINE - Sour grapes
DASH - Run between words

AAAA
B##C
B##C
BBCC

Lorem ipsum
""")
    with pytest.raises(ValueError, match='Expected 4 sections, found 5.'):
        Puzzle.parse(source_file)


def test_fewer_sections():
    source_file = StringIO("""\
Puzzle With Fewer

WORD
I##A
N##S
EACH

-
""")
    puzzle = Puzzle.parse(source_file)

    assert len(puzzle.all_clues) == 4
    assert len(puzzle.blocks) == 1  # Unused


def test_missing_definitions():
    source_file = StringIO("""\
Title

WORD
I##A
N##S
EACH

WORD - Part of a sentence

AAAA
B##C
B##C
BBCC
""")
    puzzle = Puzzle.parse(source_file)

    assert puzzle.across_clues[1] == '3. '


def test_bad_definitions():
    source_file = StringIO("""\
Bad Defs

WORD
I##A
N##S
EACH

WORD = Part of a sentence
EACH - One at a time

AAAA
B##C
B##C
BBCC
""")
    puzzle = Puzzle.parse(source_file)

    assert puzzle.all_clues == {'EACH': 'One at a time',
                                'WORD': '',
                                'WINE': '',
                                'DASH': ''}


def test_extra_definitions():
    source_file = StringIO("""\
Extra Defs

WORD
I##A
N##S
EACH

WORD - Part of a sentence
EACH - One at a time
WINE - Sour grapes
DOOM - Will be removed
DASH - Run between words

AAAA
B##C
B##C
BBCC
""")
    puzzle = Puzzle.parse(source_file)

    assert puzzle.all_clues == {'EACH': 'One at a time',
                                'WORD': 'Part of a sentence',
                                'WINE': 'Sour grapes',
                                'DASH': 'Run between words'}


def test_parse_updates_old_clues():
    clues_text = """\
WORD - Part of a sentence
EACH - One at a time
WINE - Sour grapes
DASH - Run between words
"""
    old_clues = {}
    Puzzle.parse_sections('', '', clues_text, '', old_clues)

    assert old_clues == {'EACH': 'One at a time',
                         'WORD': 'Part of a sentence',
                         'WINE': 'Sour grapes',
                         'DASH': 'Run between words'}


def test_parse_includes_old_clues():
    grid_text = """\
WORD
I##A
N##S
EACH
"""
    clues_text = """\
WORD - Part of a sentence
DASH - Run between words
"""
    old_clues = {'EACH': 'One at a time', 'OTHER': 'Unrelated'}
    puzzle = Puzzle.parse_sections('', grid_text, clues_text, '', old_clues)

    assert old_clues == {'EACH': 'One at a time',
                         'WORD': 'Part of a sentence',
                         'DASH': 'Run between words',
                         'OTHER': 'Unrelated'}
    assert puzzle.all_clues == {'EACH': 'One at a time',
                                'WORD': 'Part of a sentence',
                                'DASH': 'Run between words',
                                'WINE': ''}


def test_resize():
    puzzle = parse_basic_puzzle()

    puzzle.square_size = 100

    assert puzzle.grid[1, 0].size == 100
    assert puzzle.grid[1, 0].x == 100
    assert puzzle.grid[0, 2].y == 200
    assert puzzle.blocks[0].squares[0].size == 100


def test_display_block_sizes():
    source_file = StringIO("""\
Title

WORD
I##A
NO#S
EACH

-

AABB
A##B
DD#B
CCCC
""")
    puzzle = Puzzle.parse(source_file)

    block_sizes = puzzle.display_block_sizes()

    assert block_sizes == '2x4, A=3, D=2'


def test_display_block_sizes_all_correct():
    source_file = StringIO("""\
Title

WORD
I##A
N##S
EACH

-

AABB
A##B
A##B
CCCC
""")
    puzzle = Puzzle.parse(source_file)

    block_sizes = puzzle.display_block_sizes()

    assert block_sizes == '3x4'


def test_display_block_sizes_no_blocks():
    source_file = StringIO("""\
Title

WORD
I##A
NO#S
EACH
""")
    puzzle = Puzzle.parse(source_file)

    block_sizes = puzzle.display_block_sizes()

    assert block_sizes == 'unused=13'


def test_display_block_sizes_four_unused():
    source_file = StringIO("""\
Title

WORD
I##A
N##S
EACH

-

AAAA
####
####
BBBB
""")
    puzzle = Puzzle.parse(source_file)

    block_sizes = puzzle.display_block_sizes()

    assert block_sizes == '2x4, unused=4'


def test_draw_blocks(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        180, 180,
        'test_puzzle_draw_blocks')

    puzzle1 = parse_basic_puzzle()
    puzzle1.square_size = 20
    block1, block2, block3 = puzzle1.blocks
    block1.x = 20
    block1.y = 20
    block2.x = 70
    block2.y = 20
    block3.x = 20
    block3.y = 90
    block1.draw(expected)
    block2.draw(expected)
    block3.draw(expected)

    puzzle2 = parse_basic_puzzle()
    puzzle2.draw_blocks(actual, square_size=20)

    pixmap_differ.assert_equal()


def test_draw_clues(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        400, 180,
        'test_puzzle_draw_clues')

    puzzle = parse_basic_puzzle()
    across_clue1, across_clue2 = puzzle.across_clues
    down_clue1, down_clue2 = puzzle.down_clues

    font = expected.font()
    font.setPixelSize(22)
    expected.setFont(font)
    expected.drawText(0, 0, 400, 30, Qt.AlignHCenter, 'Basic Puzzle')
    font.setPixelSize(11)
    expected.setFont(font)
    expected.drawText(15,
                      45,
                      'Clue numbers are shuffled: 1 Across might not be in the '
                      'top left.')
    expected.drawText(15, 60, 'Across')
    expected.drawText(15, 75, across_clue1)
    expected.drawText(15, 90, across_clue2)
    expected.drawText(200, 60, 'Down')
    expected.drawText(200, 75, down_clue1)
    expected.drawText(200, 90, down_clue2)

    expected.drawText(0, 150,
                      400, 30,
                      Qt.AlignHCenter,
                      'https://donkirkby.github.io/four-letter-blocks')

    puzzle.draw_clues(actual, square_size=30)

    pixmap_differ.assert_equal()


def test_format_grid():
    puzzle = parse_basic_puzzle()
    expected_text = """\
WORD
I##A
N##S
EACH"""

    grid_text = puzzle.format_grid()

    assert grid_text == expected_text


def test_format_clues():
    puzzle = parse_basic_puzzle()
    expected_text = """\
DASH - Run between words
EACH - One at a time
WINE - Sour grapes
WORD - Part of a sentence"""

    clues_text = puzzle.format_clues()

    assert clues_text == expected_text


def test_format_blocks():
    puzzle = parse_basic_puzzle()
    expected_text = """\
AABB
A##B
A##B
CCCC"""

    blocks_text = puzzle.format_blocks()

    assert blocks_text == expected_text


def test_format_blocks_unused(monkeypatch):
    source_file = StringIO("""\
Title

WORD
I##A
N##S
EACH

-

AAAA
""")
    puzzle = Puzzle.parse(source_file)
    expected_text = """\
AAAA
?##?
?##?
????"""

    blocks_text = puzzle.format_blocks()

    assert blocks_text == expected_text


def test_shuffle(monkeypatch):
    monkeypatch.setattr(four_letter_blocks.puzzle, 'shuffle', reverse)
    puzzle = parse_basic_puzzle()
    expected_text = """\
CCBB
C##B
C##B
AAAA"""

    puzzle.shuffle()
    grid_text = puzzle.format_blocks()

    assert grid_text == expected_text
