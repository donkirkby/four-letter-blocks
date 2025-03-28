from collections import Counter
from io import StringIO
from textwrap import dedent

import pytest
from PySide6.QtGui import QTextDocument, QPainter

from four_letter_blocks.clue import Clue
from four_letter_blocks.puzzle import Puzzle, RotationsDisplay
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


def test_parse_includes_old_blocks():
    grid_text1 = dedent("""\
        WORD
        I##A
        N##S
        EACH""")
    block_text1 = dedent("""\
        AAAA
        B##C
        B##C
        BBCC""")
    grid_text2 = dedent("""\
        WRD
        I##A
        N##S
        EACH""")

    old_blocks = []
    puzzle1 = Puzzle.parse_sections('',
                                    grid_text1,
                                    '',
                                    block_text1,
                                    old_blocks=old_blocks)
    puzzle2 = Puzzle.parse_sections('',
                                    grid_text2,
                                    '',
                                    puzzle1.format_blocks(),
                                    old_blocks=old_blocks)
    puzzle3 = Puzzle.parse_sections('',
                                    grid_text1,
                                    '',
                                    puzzle2.format_blocks(),
                                    old_blocks=old_blocks)
    
    assert puzzle3.format_blocks() == puzzle1.format_blocks()


def test_parse_can_force_unused():
    grid_text1 = dedent("""\
        WORD
        I##A
        N##S
        EACH""")
    block_text1 = dedent("""\
        AAAA
        B##C
        B##C
        BBCC""")
    block_text2 = dedent("""\
        AA?A
        B##C
        B##C
        BBCC""")

    old_blocks = []
    puzzle1 = Puzzle.parse_sections('',
                                    grid_text1,
                                    '',
                                    block_text1,
                                    old_blocks=old_blocks)
    puzzle2 = Puzzle.parse_sections('',
                                    puzzle1.format_grid(),
                                    '',
                                    block_text2,
                                    old_blocks=old_blocks)

    assert puzzle2.format_blocks() == block_text2


def test_resize():
    puzzle = parse_basic_puzzle()

    puzzle.square_size = 100

    assert puzzle.grid[1, 0].size == 100
    assert puzzle.grid[1, 0].x == 100
    assert puzzle.grid[0, 2].y == 200
    assert puzzle.blocks[0].squares[0].size == 100


def test_display_block_summary():
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

    block_summary = puzzle.display_block_summary()

    assert block_summary == 'Block sizes: 2x4, A=3, D=2, Shapes: I: 1, L: 1'


def test_display_block_summary_with_rotations():
    source_file = StringIO("""\
Title

X#XX
XXX#
XX#X
XXXX

-

D#BB
DBB#
DD#C
ACCC
""")
    puzzle = Puzzle.parse(source_file)
    puzzle.rotations_display = RotationsDisplay.FRONT

    block_summary = puzzle.display_block_summary()

    assert block_summary == 'Block sizes: 3x4, A=1, Shapes: L0: 1, L1: 1, S0: 1'


def test_display_block_summary_with_rotations_back():
    source_file = StringIO("""\
Title

XX#X
#XXX
X#XX
XXXX

-

BB#D
#BBD
C#DD
CCCA
""")
    puzzle = Puzzle.parse(source_file)
    puzzle.rotations_display = RotationsDisplay.BACK

    block_summary = puzzle.display_block_summary()

    assert block_summary == 'Block sizes: 3x4, A=1, Shapes: L0: 1, L1: 1, S0: 1'


def test_shape_counts():
    source_file = StringIO("""\
Title

XX#X
#XXX
X#XX
XXXX

-

BB#D
#BBD
C#DD
CCCA
""")
    puzzle = Puzzle.parse(source_file)

    counts = puzzle.shape_counts

    assert counts == Counter({'J': 2, 'Z': 1})


def test_flipped_shape_counts():
    source_file = StringIO("""\
Title

XX#X
#XXX
X#XX
XXXX

-

BB#D
#BBD
C#DD
CCCA
""")
    puzzle = Puzzle.parse(source_file)

    counts = puzzle.flipped_shape_counts

    assert counts == Counter({'L': 2, 'S': 1})


def test_flipped_shape_counts_no_rotation():
    source_file = StringIO("""\
Title

XX#XXX
#XXXXX
X#XXX#
XXXXXX
#####X
######

-

BB#DEE
#BBDEE
C#DDF#
CCCAFF
#####F
######
""")
    x = """\
EED#BB
EEDBB#
#FDD#C
FFACCC
F#####
######
"""
    puzzle = Puzzle.parse(source_file)
    puzzle.rotations_display = RotationsDisplay.FRONT

    counts = puzzle.flipped_shape_counts

    assert counts == Counter({'L0': 1, 'L1': 1, 'S0': 1, 'O': 1, 'Z1': 1})


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

    block_summary = puzzle.display_block_summary()

    assert block_summary == 'Block sizes: unused=13'


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


def test_warning_complete_across():
    source_file = StringIO("""\
Title

WORD
I##A
N##S
EACH

-

AAAA
B##C
B##C
BBCC
""")
    puzzle = Puzzle.parse(source_file)

    warnings = puzzle.check_style()

    assert warnings == ['complete word on one block from (1, 1) to (4, 1)']


def test_warning_complete_down():
    source_file = StringIO("""\
Title

WORD
I##A
N##S
EACH

-

AAAC
A##C
B##C
BBBC
""")
    puzzle = Puzzle.parse(source_file)

    warnings = puzzle.check_style()

    assert warnings == ['complete word on one block from (4, 1) to (4, 4)']


def test_warning_complete_unused():
    source_file = StringIO("""\
Title

WORD
I##A
N##S
EACH
""")
    puzzle = Puzzle.parse(source_file)

    warnings = puzzle.check_style()

    assert warnings == []


def test_warning_two_letter():
    source_file = StringIO("""\
Title

WORD
I#OA
NO#S
ENDS
""")
    puzzle = Puzzle.parse(source_file)

    warnings = puzzle.check_style()

    assert warnings == ['two-letter word at (1, 3) and (2, 3)',
                        'two-letter word at (2, 3) and (2, 4)',
                        'two-letter word at (3, 1) and (3, 2)',
                        'two-letter word at (3, 2) and (4, 2)']


def test_warning_square():
    source_file = StringIO("""\
Title

WON
I##
NO#
END
""")
    puzzle = Puzzle.parse(source_file)

    warnings = puzzle.check_style()

    assert warnings == ['not square',
                        'two-letter word at (1, 3) and (2, 3)',
                        'two-letter word at (2, 3) and (2, 4)']


def test_warning_symmetry():
    source_file = StringIO("""\
Title

WE#D
I##A
N##D
ENDS
""")
    puzzle = Puzzle.parse(source_file)

    warnings = puzzle.check_style()

    assert warnings == ['symmetry broken at (2, 4) and (3, 1)',
                        'two-letter word at (1, 1) and (2, 1)']


def test_warning_symmetry_diagonal():
    source_file = StringIO("""\
Title

WEED
I##A
N##D
END#
""")
    puzzle = Puzzle.parse(source_file)

    warnings = puzzle.check_style()

    assert warnings == ['symmetry broken at (1, 1) and (4, 4)']


def test_warning_symmetry_vertical():
    source_file = StringIO("""\
Title

WED
I#A
N#D
""")
    puzzle = Puzzle.parse(source_file)

    warnings = puzzle.check_style()

    assert warnings == ['symmetry broken at (2, 1) and (2, 3)']


def test_warning_repeat():
    source_file = StringIO("""\
Title

REED
E##E
E##A
DEED
""")
    puzzle = Puzzle.parse(source_file)

    warnings = puzzle.check_style()

    assert warnings == ['repeated word REED']


def test_draw_blocks(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(150, 180) as (actual, expected):
        puzzle1 = parse_basic_puzzle()
        puzzle1.square_size = 20
        block1, block2, block3 = puzzle1.blocks
        block1.x = 20
        block1.y = 50
        block2.x = 70
        block2.y = 50
        block3.x = 20
        block3.y = 20
        block1.draw(expected)
        block2.draw(expected)
        block3.draw(expected)

        puzzle2 = parse_basic_puzzle()
        puzzle2.draw_blocks(actual, square_size=20)


def test_draw_blocks_one_row(pixmap_differ: PixmapDiffer):
    with pixmap_differ.create_painters(150, 180):
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter
        puzzle1 = parse_basic_puzzle()
        puzzle1.square_size = 20
        block1, block2, block3 = puzzle1.blocks
        block1.x = 20
        block1.y = 10
        block1.draw(expected)
        block2.x = 70
        block2.y = 10
        block2.draw(expected)

        puzzle2 = parse_basic_puzzle()
        puzzle2.draw_blocks(actual, square_size=20, row_index=1)


def test_draw_clues(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(400, 180) as (actual, expected):
        puzzle = parse_basic_puzzle()
        puzzle.across_clues[0] = Clue('Part of a long run-on sentence that really '
                                      'desperately needs to wrap',
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
        expected_doc.setHtml(dedent("""\
            <h1>Basic Puzzle</h1>
            <p>Clue numbers are shuffled: 1 Across might not be the top left. 3 pieces.</p>
            <hr>
            <table>
            <tr><td>Across</td><td>Down</td></tr>
            <tr><td>
              <table>
              <tr><td class="num">1.</td>
                <td>Part of a long run-on sentence that really desperately needs to wrap</td></tr>
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
        """))
        expected_doc.drawContents(expected)

        actual_doc = QTextDocument()
        actual_doc.setDefaultFont(font)
        actual_doc.setPageSize(actual.window().size())

        puzzle.build_clues(actual_doc)

        actual_doc.drawContents(actual)


def test_draw_clues_with_reference(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(400, 180) as (actual, expected):
        source_file = StringIO(dedent("""\
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
            """))
        puzzle = Puzzle.parse(source_file)

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
        expected_doc.setHtml(dedent("""\
            <h1>Basic Puzzle</h1>
            <p>Clue numbers are shuffled: 1 Across might not be the top left. 3 pieces.</p>
            <hr>
            <table>
            <tr><td>Across</td><td>Down</td></tr>
            <tr><td>
              <table>
              <tr><td class="num">1.</td>
                <td>Part of a sentence</td></tr>
              <tr><td class="num">3.</td>
                <td>One at a time</td></tr>
              </table>
            </td><td>
              <table>
              <tr><td class="num">1.</td>
                <td>Sour grapes</td></tr>
              <tr><td class="num">2.</td>
                <td>Run between 1 Across and a neighbour</td></tr>
              </table>
            </td></tr>
            </table>
            <hr class="footer">
            <p><center><a href="#">https://donkirkby.github.io/four-letter-blocks</a></center></p>
            <p></p>
            """))
        expected_doc.drawContents(expected)

        actual_doc = QTextDocument()
        actual_doc.setDefaultFont(font)
        actual_doc.setPageSize(actual.window().size())

        puzzle.build_clues(actual_doc)

        actual_doc.drawContents(actual)


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


def test_format_clues_with_reference():
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
    expected_text = """\
DASH - Run between WORD and a neighbour
EACH - One at a time
WINE - Sour grapes
WORD - Part of a sentence"""
    puzzle = Puzzle.parse(source_file)

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


def test_extras():
    text = dedent("""\
        AAFFF
        BAAEF
        BC#EE
        BCCED
        BCDDD""")
    expected_extras = 'I+, Z+1'
    puzzle = Puzzle.parse_sections('', text, '', text)

    assert puzzle.extras == expected_extras
