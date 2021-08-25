from io import StringIO

import pytest
from PySide6.QtGui import QTextDocument

from four_letter_blocks.clue import Clue
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
    assert puzzle.across_clues[1].format() == '3. One at a time'
    assert puzzle.all_clues['EACH'].text == 'One at a time'


def test_parse_clue_with_reference():
    source_file = StringIO("""\
Basic Puzzle

WORD
I##A
N##S
EACH

WORD - Part of a sentence
EACH - One at a time
WINE - Sour grapes
DASH - Run between WORD and a neighbour

AABB
A##B
A##B
CCCC
""")
    puzzle = Puzzle.parse(source_file)

    assert puzzle.down_clues[1].format() == '2. Run between 1 Across and a neighbour'


def test_parse_clue_with_unknown_reference():
    source_file = StringIO("""\
Basic Puzzle

WORD
I##A
N##S
EACH

WORD - Part of a sentence
EACH - One at a time
WINE - Sour grapes
DASH - Run between WHAT and a neighbour

AABB
A##B
A##B
CCCC
""")
    puzzle = Puzzle.parse(source_file)

    assert puzzle.down_clues[1].format() == '2. Run between WHAT and a neighbour'


def test_parse_clue_with_two_references():
    source_file = StringIO("""\
Basic Puzzle

WORD
I##A
N##S
EACH

WORD - Part of a sentence
EACH - One at a time
WINE - Sour grapes
DASH - Run between WORD and WINE

AABB
A##B
A##B
CCCC
""")
    puzzle = Puzzle.parse(source_file)

    assert puzzle.down_clues[1].format() == '2. Run between 1 Across and 1 Down'


def test_parse_with_suits():
    source_file = StringIO("""\
Title

ABCDEFGHIJKL
A##########L
BZZZZ######M
B##########M
C##########N
C##########N
D##########O
D##########O
E##########P
E##########P
F##########Q
FGHIJKLMNOPQ

ABCDEFGHIJKL - Half an alphabet?
FGHIJKLMNOPQ - Later
BZZZZ - Noisy bee

AAAABBBBCCCC
K##########D
KLLLL######D
K##########D
K##########D
J##########E
J##########E
J##########E
J##########E
I##########F
I##########F
IIHHHHGGGGFF
""")
    puzzle = Puzzle.parse(source_file)

    assert puzzle.grid[0, 0].suit == 'C'
    assert puzzle.across_clues[0].format() == '1♣. Half an alphabet?'

    # Block comes after bottom-left corner, but suits are grouped together.
    assert puzzle.across_clues[1].format() == '2♣. Noisy bee'

    # No words in bottom-right quadrant, so bottom-left uses hearts.
    assert puzzle.across_clues[2].format() == '1♡. Later'


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

    assert puzzle.across_clues[1].format() == '3. '


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

    assert puzzle.all_clues == {'EACH': Clue('One at a time', 3),
                                'WORD': Clue('', 1),
                                'WINE': Clue('', 1),
                                'DASH': Clue('', 2)}


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

    assert puzzle.all_clues == {'EACH': Clue('One at a time', 3),
                                'WORD': Clue('Part of a sentence', 1),
                                'WINE': Clue('Sour grapes', 1),
                                'DASH': Clue('Run between words', 2)}


def test_parse_updates_old_clues():
    clues_text = """\
WORD - Part of a sentence
EACH - One at a time
WINE - Sour grapes
DASH - Run between words
"""
    old_clues = {}
    Puzzle.parse_sections('', '', clues_text, '', old_clues)

    assert old_clues == {'EACH': Clue('One at a time'),
                         'WORD': Clue('Part of a sentence'),
                         'WINE': Clue('Sour grapes'),
                         'DASH': Clue('Run between words')}


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
    old_clues = {'EACH': Clue('One at a time'), 'OTHER': Clue('Unrelated')}
    puzzle = Puzzle.parse_sections('', grid_text, clues_text, '', old_clues)

    assert old_clues == {'EACH': Clue('One at a time', 3),
                         'WORD': Clue('Part of a sentence', 1),
                         'DASH': Clue('Run between words', 2),
                         'OTHER': Clue('Unrelated')}
    assert puzzle.all_clues == {'EACH': Clue('One at a time', 3),
                                'WORD': Clue('Part of a sentence', 1),
                                'DASH': Clue('Run between words', 2),
                                'WINE': Clue('', 1)}


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


def test_draw_blocks_one_row(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        180, 180,
        'test_puzzle_draw_blocks_one_row')

    puzzle1 = parse_basic_puzzle()
    puzzle1.square_size = 20
    block1, block2, block3 = puzzle1.blocks
    block3.x = 20
    block3.y = 10
    block3.draw(expected)

    puzzle2 = parse_basic_puzzle()
    puzzle2.draw_blocks(actual, square_size=20, row_index=1)

    pixmap_differ.assert_equal()


def test_draw_clues(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        400, 180,
        'test_puzzle_draw_clues')

    puzzle = parse_basic_puzzle()
    puzzle.across_clues[0] = Clue('Part of a long run-on sentence that really '
                                  'needs to wrap',
                                  1)

    expected_doc = QTextDocument()
    expected_doc.setPageSize(expected.window().size())
    font = expected_doc.defaultFont()
    font.setPixelSize(9)
    expected_doc.setDefaultFont(font)
    expected_doc.setDefaultStyleSheet("""\
h1 {text-align: center}
hr.footer {line-height:10px}
p.footer {page-break-after: always}
td {padding: 1px }
td.num {text-align: right}
a {color: black}
""")
    expected_doc.setHtml("""\
<h1>Basic Puzzle</h1>
<p>Clue numbers are shuffled: 1 Across might not be in the top left.</p>
<hr>
<table>
<tr><td>Across</td><td>Down</td></tr>
<tr><td>
  <table>
  <tr><td class="num">1.</td>
    <td>Part of a long run-on sentence that really needs to wrap</td></tr>
  <tr><td class="num">3.</td>
    <td>One at a time</td></tr>
  </table>
</td><td>
  <table>
  <tr><td class="num">1.</td>
    <td>Sour grapes</td></tr>
  <tr><td class="num">2.</td>
    <td>Run between words</td></tr>
  </table>
</td></tr>
</table>
<hr class="footer">
<p><center><a href="#">https://donkirkby.github.io/four-letter-blocks</a></center></p>
<p></p>
""")
    expected_doc.drawContents(expected)

    actual_doc = QTextDocument()
    actual_doc.setDefaultFont(font)
    actual_doc.setPageSize(actual.window().size())

    puzzle.build_clues(actual_doc)

    actual_doc.drawContents(actual)

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


def test_format_blocks_unused():
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
