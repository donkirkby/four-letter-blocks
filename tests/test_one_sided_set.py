from io import StringIO
from textwrap import dedent

import yaml
from PySide6.QtGui import QPainter, QColor

from four_letter_blocks.block import Block
from four_letter_blocks.one_sided_set import OneSidedSet
from four_letter_blocks.puzzle import Puzzle
from four_letter_blocks.square import Square
from tests.pixmap_differ import PixmapDiffer


def parse_puzzle_set(set_options_yaml: str | None = None) -> OneSidedSet:
    puzzle1 = Puzzle.parse(StringIO(dedent("""\
        Example 1

        #ABC#
        DEFGH
        IJ#KL
        MNOWQ
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
        MNOXQ
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
        LMNOY
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
        DEFZH
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

    if set_options_yaml is None:
        set_options_yaml = """
            packing_pages:
                - |
                    A.BCCCD.
                    ABB.ECD.
                    AABEEEDD
                    .FGGG..H
                    FFIIGJHH
                    FII.JJJH
                - |
                    AABBBCCD
                    AAEB.CCD
                    FEEGGG.D
                    FFEHGIID
                    FJJHH.II
                    .JJ.H...
        """
    set_options = yaml.safe_load(set_options_yaml)

    puzzle_set = OneSidedSet(puzzle2,
                             puzzle3,
                             puzzle4,
                             puzzle1,
                             set_options=set_options,
                             frame_lengths=((5, 2), (5,)))
    puzzle_set.pack_puzzles()
    return puzzle_set


def test_draw_page1(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(
            360,
            180) as (actual, expected):
        expected_puzzle_set = parse_puzzle_set()
        expected_puzzle_set.square_size = 20
        blocks1 = expected_puzzle_set.puzzles[0].blocks
        blocks1[0].x, blocks1[0].y = 40, 100
        blocks1[1].x, blocks1[1].y = 40, 20
        blocks1[2].x, blocks1[2].y = 20, 20
        blocks1[3].x, blocks1[3].y = 80, 20
        blocks1[4].x, blocks1[4].y = 140, 80
        blocks2 = expected_puzzle_set.puzzles[1].blocks
        blocks2[0].x, blocks2[0].y = 80, 40
        blocks2[1].x, blocks2[1].y = 60, 80
        blocks2[2].x, blocks2[2].y = 20, 80
        blocks2[3].x, blocks2[3].y = 100, 100
        blocks2[4].x, blocks2[4].y = 140, 20

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
        for block.x, block.y in [(40, 20),
                                 (160, 20),
                                 (80, 40),
                                 (160, 40),
                                 (20, 80),
                                 (120, 80),
                                 (140, 80),
                                 (80, 120)]:
            block.draw(expected, is_packed=True)
            block.draw_outline(expected)

        expected.setPen(block.CUT_COLOUR)
        expected.drawLine(20, 20, 10, 20)
        expected.drawLine(10, 20, 10, 10)
        expected.drawLine(10, 10, 120, 10)
        expected.drawLine(120, 10, 120, 20)

        expected.drawLine(120, 10, 160, 10)
        expected.drawLine(160, 10, 160, 20)

        expected.drawLine(180, 20, 180, 10)
        expected.drawLine(180, 10, 190, 10)
        expected.drawLine(190, 10, 190, 120)
        expected.drawLine(190, 120, 180, 120)

        expected.drawLine(180, 140, 190, 140)
        expected.drawLine(190, 140, 190, 150)
        expected.drawLine(190, 150, 80, 150)
        expected.drawLine(80, 150, 80, 140)

        expected.drawLine(80, 150, 40, 150)
        expected.drawLine(40, 150, 40, 140)

        expected.drawLine(20, 140, 20, 150)
        expected.drawLine(20, 150, 10, 150)
        expected.drawLine(10, 150, 10, 40)
        expected.drawLine(10, 40, 20, 40)

        actual_puzzle_set = parse_puzzle_set()

        assert actual_puzzle_set.page_count == 2

        actual_puzzle_set.square_size = 20
        actual_puzzle_set.draw_front(actual)
        actual_puzzle_set.draw_cuts(actual)


def test_draw_page2(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(
            360,
            180) as (actual, expected):
        expected_puzzle_set = parse_puzzle_set()
        expected_puzzle_set.square_size = 20
        blocks1 = expected_puzzle_set.puzzles[2].blocks
        blocks1[0].x, blocks1[0].y = 150, 10
        blocks1[1].x, blocks1[1].y = 10, 10
        blocks1[2].x, blocks1[2].y = 70, 70
        blocks1[3].x, blocks1[3].y = 30, 30
        blocks1[4].x, blocks1[4].y = 10, 50
        blocks2 = expected_puzzle_set.puzzles[3].blocks
        blocks2[0].x, blocks2[0].y = 50, 10
        blocks2[1].x, blocks2[1].y = 110, 10
        blocks2[2].x, blocks2[2].y = 110, 70
        blocks2[3].x, blocks2[3].y = 70, 50
        blocks2[4].x, blocks2[4].y = 30, 90

        for block in blocks1 + blocks2:
            block.tab_count = 1
            block.border_colour = block.CUT_COLOUR
            block.draw(expected, is_packed=True)
            block.draw_outline(expected)
        square = Square(' ')
        square.size = 20
        block = Block(square)
        block.tab_count = 1
        block.border_colour = block.CUT_COLOUR
        block.face_colour = QColor('black')
        for block.x, block.y in [(90, 30),
                                 (130, 50),
                                 (110, 90),
                                 (10, 110),
                                 (70, 110),
                                 (110, 110),
                                 (130, 110),
                                 (150, 110)]:
            block.draw(expected, is_packed=True)
            block.draw_outline(expected)

        actual_puzzle_set = parse_puzzle_set()
        actual_puzzle_set.page_index = 1
        actual_puzzle_set.pack_puzzles()

        actual_puzzle_set.square_size = 20
        actual_puzzle_set.draw_front(actual)
        actual_puzzle_set.draw_cuts(actual)
