from io import StringIO

import pytest

from four_letter_blocks.puzzle import Puzzle


def test_parse():
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

    assert puzzle.grid[0, 0].letter == 'W'
    assert puzzle.across_clues['WORD'] == 'Part of a sentence'


def test():
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
