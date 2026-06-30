from collections import Counter
from io import StringIO
from pathlib import Path
from textwrap import dedent

import pytest
import yaml
from PySide6.QtGui import QPainter, QPixmap, QImage, QColor
from colorspacious import cspace_convert

from four_letter_blocks.block import Block
from four_letter_blocks.puzzle import Puzzle
from four_letter_blocks.puzzle_set import PuzzleSet
from four_letter_blocks import four_letter_blocks_rc
from four_letter_blocks.square import Square
from tests.pixmap_differ import PixmapDiffer

assert four_letter_blocks_rc  # Need to import this module to load resources.


def parse_puzzle_set(set_options_yaml: str | None = None) -> PuzzleSet:
    puzzle1 = Puzzle.parse(StringIO(dedent("""\
        Example 1

        #ABC#
        DEFG#
        HIJKL
        MNOWQ
        #RST#

        -

        #DCC#
        DDCC#
        DAAAA
        IIIGG
        #IGG#
        """)))
    puzzle2 = Puzzle.parse(StringIO(dedent("""\
        Example 2

        #ABC#
        DEFG#
        HIJKL
        MNOWQ
        #RST#

        -

        #FEE#
        FFEE#
        FBBBB
        JJJHH
        #JHH#
        """)))
    puzzle3 = Puzzle.parse(StringIO(dedent("""\
        Example 3

        #ABC#
        #DEFG
        HIJKL
        MNOWQ
        #RST#

        -

        #CCD#
        #CCDD
        AAAAD
        GGIII
        #GGI#
        """)))
    puzzle4 = Puzzle.parse(StringIO(dedent("""\
        Example 4

        #ABC#
        #DEFG
        HIJKL
        MNOWQ
        #RST#

        -

        #EEF#
        #EEFF
        BBBBF
        HHJJJ
        #HHJ#
        """)))

    if set_options_yaml is None:
        set_options_yaml = """
            packing_pages:
                - |
                    EEEFDDDD
                    #EFFCCCC
                    #GFJJJBB
                    GG##J#BB
                    GHHII#AA
                    HHII##AA
        """
    set_options = yaml.safe_load(set_options_yaml)

    puzzle_set = PuzzleSet(puzzle1,
                           puzzle2,
                           puzzle3,
                           puzzle4,
                           set_options=set_options,
                           frame_lengths=((5, 2), (5,)))
    puzzle_set.pack_puzzles()
    return puzzle_set


def test_empty_set():
    puzzle_set = PuzzleSet()
    puzzle_set.pack_puzzles()

    assert puzzle_set.block_summary == '0 blocks'


def test_summary():
    puzzle_set = parse_puzzle_set()
    puzzle1, puzzle2, puzzle3, puzzle4 = puzzle_set.puzzles

    summary1 = puzzle1.display_block_summary()
    assert summary1 == 'Block sizes: 5x4, Shapes: I1: 1, O: 1, S0: 1, T0: 1, Z1: 1'
    summary3 = puzzle2.display_block_summary()  # Flipped shapes.
    assert summary3 == 'Block sizes: 5x4, Shapes: I1: 1, O: 1, S0: 1, T0: 1, Z1: 1'

    set_summary = puzzle_set.block_summary
    assert set_summary == '20 blocks'


def test_summary_of_three():
    """ Max count is fine, but uneven total O's """
    squares_text = dedent("""\
        Title

        ABCD
        EFGH
        IJKL
        MNOP

        -

        AABB
        AABB
        CCDD
        CCDD
    """)
    puzzle1 = Puzzle.parse(StringIO(squares_text))
    puzzle2 = Puzzle.parse(StringIO(squares_text))
    puzzle3 = Puzzle.parse(StringIO(dedent("""\
        Title
        
        ABCDE
        FG##H
        IJ#KL
        M##NO
        PQRST
        
        -
        
        BBBBC
        AA##C
        AA#DC
        E##DC
        EEEDD
    """)))
    with pytest.raises(ValueError) as info:
        PuzzleSet(puzzle1, puzzle2, puzzle3)

    expected_message = ("No combination of unused counts and shape counts "
                        "could be evenly split: (0, 0, 0); O: 4; O: 4; I0: 1, "
                        "I1: 1, J3: 1, L0: 1, O: 1.")
    assert info.value.args == (expected_message,)


def test_summary_no_extras():
    squares_text = dedent("""\
        Title

        ABCD
        EFGH
        IJKL
        MNOP

        -

        AABB
        AABB
        CCDD
        CCDD
    """)
    puzzle1 = Puzzle.parse(StringIO(squares_text))
    puzzle2 = Puzzle.parse(StringIO(squares_text))
    puzzle_set = PuzzleSet(puzzle1, puzzle2)
    puzzle_set.pack_puzzles()

    set_summary = puzzle_set.block_summary
    assert set_summary == '8 blocks'


def test_shape_counts():
    puzzle_set = parse_puzzle_set()

    shape_counts = puzzle_set.shape_counts

    assert shape_counts == Counter({'I1': 2, 'O': 2, 'S0': 2, 'T0': 2, 'Z1': 2})


def test_draw_background(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(350, 180) as (actual, expected):
        tile = QPixmap(100, 100)
        painter = QPainter(tile)
        try:
            painter.setBackground(QColor('burlywood'))
            painter.eraseRect(painter.window())
            painter.fillRect(25, 25, 50, 50, 'tan')
        finally:
            painter.end()
        expected.drawPixmap(0, 0, tile)
        expected.drawPixmap(100, 0, tile)
        expected.drawPixmap(200, 0, tile)
        expected.drawPixmap(300, 0, tile)
        expected.drawPixmap(0, 100, tile)
        expected.drawPixmap(100, 100, tile)
        expected.drawPixmap(200, 100, tile)
        expected.drawPixmap(300, 100, tile)

        puzzle_set = parse_puzzle_set()
        puzzle_set.draw_background(actual, tile)


def test_draw_packed(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(
            360,
            180,
            'test_puzzle_draw_packed') as (actual, expected):
        expected_puzzle_set = parse_puzzle_set()

        puzzle1 = expected_puzzle_set.puzzles[0]
        expected.fillRect(expected.window(), puzzle1.face_colour)
        actual.fillRect(expected.window(), puzzle1.face_colour)

        expected_puzzle_set.square_size = 20
        blocks1 = expected_puzzle_set.puzzles[0].blocks
        blocks1[0].set_display(100, 20, 1)
        blocks1[1].set_display(140, 60, 0)
        blocks1[2].set_display(20, 60, 1)
        blocks1[3].set_display(60, 100, 0)
        blocks1[4].set_display(80, 60, 0)
        blocks2 = expected_puzzle_set.puzzles[1].blocks
        blocks2[0].set_display(100, 40, 1)
        blocks2[1].set_display(140, 100, 0)
        blocks2[2].set_display(60, 20, 1)
        blocks2[3].set_display(20, 100, 0)
        blocks2[4].set_display(20, 20, 0)
        blocks3 = expected_puzzle_set.puzzles[2].blocks
        blocks3[0].set_display(180, 20, 1)
        blocks3[1].set_display(180, 60, 0)
        blocks3[2].set_display(300, 60, 1)
        blocks3[3].set_display(240, 100, 0)
        blocks3[4].set_display(220, 60, 0)
        blocks4 = expected_puzzle_set.puzzles[3].blocks
        blocks4[0].set_display(180, 40, 1)
        blocks4[1].set_display(180, 100, 0)
        blocks4[2].set_display(260, 20, 1)
        blocks4[3].set_display(280, 100, 0)
        blocks4[4].set_display(280, 20, 0)

        for block in blocks1 + blocks2 + blocks3 + blocks4:
            block.draw(expected, is_packed=True)
        square = Square(' ')
        square.size = 20
        block = Block(square)
        block.tab_count = 1
        block.border_colour = block.CUT_COLOUR
        block.face_colour = QColor('black')
        for block.x, block.y in [(20, 40),
                                 (20, 60),
                                 (60, 80),
                                 (80, 80),
                                 (120, 80),
                                 (120, 100),
                                 (100, 120),
                                 (120, 120)]:
            block.draw(expected, is_packed=True)
            block.x = 337 - block.x
            block.draw(expected, is_packed=True)

        puzzle_set2 = parse_puzzle_set()
        puzzle_set2.square_size = 20
        puzzle_set2.draw_front(actual)

        actual.setViewport(160, 0, 360, 180)
        puzzle_set2.draw_back(actual)


def test_draw_front(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(
            360,
            180) as (actual, expected):
        expected_puzzle_set = parse_puzzle_set()
        expected_puzzle_set.square_size = 20
        blocks1 = expected_puzzle_set.puzzles[0].blocks
        blocks1[0].set_display(100, 20, 1)
        blocks1[1].set_display(140, 60, 0)
        blocks1[2].set_display(20, 60, 1)
        blocks1[3].set_display(60, 100, 0)
        blocks1[4].set_display(80, 60, 0)
        blocks2 = expected_puzzle_set.puzzles[1].blocks
        blocks2[0].set_display(100, 40, 1)
        blocks2[1].set_display(140, 100, 0)
        blocks2[2].set_display(60, 20, 1)
        blocks2[3].set_display(20, 100, 0)
        blocks2[4].set_display(20, 20, 0)

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
        for block.x, block.y in [(20, 40),
                                 (20, 60),
                                 (60, 80),
                                 (80, 80),
                                 (120, 80),
                                 (120, 100),
                                 (100, 120),
                                 (120, 120)]:
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

        assert actual_puzzle_set.page_count == 1

        actual_puzzle_set.square_size = 20
        actual_puzzle_set.draw_front(actual)
        actual_puzzle_set.draw_cuts(actual)


# noinspection DuplicatedCode
def test_background_tile(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(500, 260) as (actual, expected):
        expected_image = QImage(Path(__file__).parent / 'set_tile.png')
        expected.drawImage(0, 0, expected_image)

        puzzle_set = parse_puzzle_set()

        actual.setBackground(puzzle_set.puzzles[0].face_colour)
        actual.eraseRect(actual.window())

        actual.setWindow(0, 0, 260, 260)
        actual.setViewport(actual.window().translated(120, 0))
        puzzle_set = parse_puzzle_set()
        puzzle_set.draw_background_tile(actual)


@pytest.mark.parametrize(
    'sizes, start_hue, expected_hues',
    # Sizes in order
    (((7, 9, 11, 13, 15), 0, (0, 72, 144, 216, 288)),
     # Sizes out of order
     ((9, 7, 11, 13, 15), 0, (72, 0, 144, 216, 288)),
     # Fewer sizes
     ((9, 10, 11, 12), 0, (0, 90, 180, 270)),
     # Nonzero start
     ((9, 10, 11, 12), 120, (120, 210, 300, 30)),
     # Repeated sizes
     ((9, 9, 11), 0, (0, 120, 240))))
def test_colours(sizes, start_hue, expected_hues):
    expected_jchs = [(77, 20, hue) for hue in expected_hues]
    puzzles = []
    for size in sizes:
        grid_text = '\n'.join(['X'*size]*size)
        puzzle = Puzzle.parse_sections(f'{size=}',
                                       grid_text,
                                       '',
                                       '')
        puzzles.append(puzzle)

    PuzzleSet.set_face_colours(puzzles, start_hue)

    colours = (puzzle.face_colour for puzzle in puzzles)
    jchs = []
    for colour in colours:
        rgb = colour.toRgb().toTuple()[:3]
        lightness, chroma, hue = cspace_convert(rgb, 'sRGB255', 'JCh')
        jchs.append((round(lightness), round(chroma), round(hue)))
    for actual_jch, expected_jch in zip(jchs, expected_jchs):
        for actual_element, expected_element in zip(actual_jch, expected_jch):
            increase = (actual_element - expected_element) % 360
            decrease = (expected_element - actual_element) % 360
            if min(increase, decrease) > 1:
                assert jchs == expected_jchs


def test_target_colours_too_dark():
    start_colour = QColor.fromRgb(0, 0, 0)
    shift = 4.0

    with pytest.raises(ValueError, match=r'Start colour is too dark'):
        PuzzleSet.get_target_colours(start_colour, shift)


def test_target_colours_too_light():
    start_colour = QColor.fromRgb(255, 255, 255)
    shift = 4.0

    with pytest.raises(ValueError, match=r'Start colour is too light'):
        PuzzleSet.get_target_colours(start_colour, shift)


def test_target_colours():
    start_colour = QColor.fromRgb(0, 0, 255)
    shift = 4.0

    with pytest.raises(ValueError, match=r'Start colour is invalid after shift'):
        PuzzleSet.get_target_colours(start_colour, shift)
