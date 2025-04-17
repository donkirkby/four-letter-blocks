import typing
from io import StringIO
from textwrap import dedent

import pytest
from PySide6.QtGui import QPainter, QColor

from four_letter_blocks.block import Block
from four_letter_blocks.one_sided_set import OneSidedSet
from four_letter_blocks.puzzle import Puzzle
from four_letter_blocks.square import Square
from tests.pixmap_differ import PixmapDiffer


def parse_puzzle_set(packing_pages: typing.IO | None = None) -> OneSidedSet:
    puzzle1 = Puzzle.parse(StringIO(dedent("""\
        Example 1

        #ABC#
        DEFGH
        IJ#KL
        MNOPQ
        #RST#
        
        -

        #AAA#
        BBAEE
        BB#EE
        CCDDD
        #CCD#
        """)))
    puzzle2 = Puzzle.parse(StringIO(dedent("""\
        Example 2

        #A#BC
        DEFGH
        IJ#KL
        MNOPQ
        RS#T#

        -

        #B#AA
        BBAAE
        CB#EE
        CDDDE
        CC#D#
        """)))
    puzzle3 = Puzzle.parse(StringIO(dedent("""\
        Example 3

        #ABCD
        EFGHI
        #J#K#
        LMNOP
        QRST#

        -

        #ABBB
        AAAFB
        #C#F#
        CCEFF
        CEEE#
        """)))
    puzzle4 = Puzzle.parse(StringIO(dedent("""\
        Example 4

        #AB#C
        DEFGH
        IJ#KL
        MNOPQ
        R#ST#

        -

        #BB#E
        ABBEE
        AD#FE
        ADDFF
        A#DF#
        """)))

    if packing_pages is None:
        packing_pages = StringIO(dedent("""\
            type: OneSidedSet
            title: Example 2
            title: Example 3
            title: Example 4
            title: Example 1
    
            A.BCCCD.
            ABB.ECD.
            AABEEEDD
            .FGGG..H
            FFIIGJHH
            FII.JJJH
    
            AABBBCCD
            AAEB.CCD
            FEEGGG.D
            FFEHGIID
            FJJHH.II
            .JJ.H..."""))

    puzzle_set = OneSidedSet(puzzle1,
                             puzzle2,
                             puzzle3,
                             puzzle4,
                             packing_pages=packing_pages,
                             frame_lengths=[5, 2])
    return puzzle_set

def test_bad_type():
    packing_pages = StringIO(dedent("""\
        type: PuzzleSet
        title: Example 1
        """))

    with pytest.raises(
            ValueError,
            match=r'Expected type OneSidedSet, but found PuzzleSet'):
        OneSidedSet(packing_pages=packing_pages)


def test_puzzle_order():
    puzzle_set = parse_puzzle_set()

    titles = [puzzle.title for puzzle in puzzle_set.puzzles]
    assert titles == ['Example 2', 'Example 3', 'Example 4', 'Example 1']


def test_puzzle_order_changed():
    packing_pages = StringIO(dedent("""\
        type: OneSidedSet
        title: Example 3
        title: Example 2
        title: Example 4
        title: Example 1
        """))
    puzzle_set = parse_puzzle_set(packing_pages)

    titles = [puzzle.title for puzzle in puzzle_set.puzzles]
    assert titles == ['Example 3', 'Example 2', 'Example 4', 'Example 1']


def test_unknown_title():
    packing_pages = StringIO(dedent("""\
        type: OneSidedSet
        title: Example 3
        title: Example 2
        title: Mystery Puzzle
        title: Example 1
        """))
    with pytest.raises(ValueError,
                       match=r'Puzzle title not found: Mystery Puzzle'):
        parse_puzzle_set(packing_pages)


def test_duplicate_title():
    packing_pages = StringIO(dedent("""\
        type: OneSidedSet
        title: Example 2
        title: Example 3
        title: Example 3
        title: Example 2
        """))
    with pytest.raises(ValueError,
                       match=r'Duplicate puzzle title: Example 3'):
        parse_puzzle_set(packing_pages)


def test_draw_cuts(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(
            360,
            180,
            'test_one_sided_set_init') as (actual, expected):
        # TODO: Pack into two 6x9 grids, with 5 & 2 frames on top & bottom of each.
        expected_puzzle_set = parse_puzzle_set()
        expected_puzzle_set.square_size = 20
        blocks1 = expected_puzzle_set.puzzles[0].blocks
        blocks1[0].x, blocks1[0].y = 30, 90
        blocks1[1].x, blocks1[1].y = 30, 10
        blocks1[2].x, blocks1[2].y = 10, 10
        blocks1[3].x, blocks1[3].y = 70, 10
        blocks1[4].x, blocks1[4].y = 130, 70
        blocks2 = expected_puzzle_set.puzzles[1].blocks
        blocks2[0].x, blocks2[0].y = 70, 30
        blocks2[1].x, blocks2[1].y = 50, 70
        blocks2[2].x, blocks2[2].y = 10, 70
        blocks2[3].x, blocks2[3].y = 90, 90
        blocks2[4].x, blocks2[4].y = 130, 10

        for block in blocks1 + blocks2:
            block.border_colour = block.CUT_COLOUR
            block.draw(expected, is_packed=True)
            block.draw_outline(expected)
        square = Square(' ')
        square.size = 20
        block = Block(square)
        block.tab_count = 1
        block.border_colour = block.CUT_COLOUR
        block.face_colour = QColor('black')
        for block.x, block.y in [(30, 10),
                                 (150, 10),
                                 (70, 30),
                                 (150, 30),
                                 (10, 70),
                                 (110, 70),
                                 (130, 70),
                                 (70, 110)]:
            block.draw(expected, is_packed=True)
            block.draw_outline(expected)


        actual_puzzle_set = parse_puzzle_set()

        assert actual_puzzle_set.page_count == 2

        actual_puzzle_set.square_size = 20
        for shape_blocks in actual_puzzle_set.front_blocks.values():
            for block in shape_blocks:
                for square in block.squares:
                    square.size = actual_puzzle_set.square_size
        actual_puzzle_set.draw_front(actual)
        actual_puzzle_set.draw_cuts(actual)
