from io import StringIO
from textwrap import dedent

import pytest

from four_letter_blocks.puzzle import Puzzle
from four_letter_blocks.puzzle_set import PuzzleSet
from tests.pixmap_differ import PixmapDiffer


def parse_puzzle_set():
    puzzle1 = Puzzle.parse(StringIO(dedent("""\
        Title

        ABCDE
        FG##H
        IJ#KL
        M##NO
        PQRST

        -

        ABBBC
        AB##C
        AA#CC
        E##DD
        EEEDD
    """)))
    puzzle2 = Puzzle.parse(StringIO(dedent("""\
        Title

        ABCDE
        FG##H
        IJ#KL
        M##NO
        PQRST

        -

        ABBBB
        AA##C
        EA#CC
        E##CD
        EEDDD
    """)))
    puzzle_set = PuzzleSet(puzzle1, puzzle2)
    return puzzle_set


def test_summary():
    puzzle_set = parse_puzzle_set()
    puzzle1, puzzle2 = puzzle_set.puzzles

    summary1 = puzzle1.display_block_summary()
    assert summary1 == 'Block sizes: 5x4, Shapes: J: 2, L: 2, O: 1'
    summary2 = puzzle2.display_block_summary()
    assert summary2 == 'Block sizes: 5x4, Shapes: I: 1, L: 2, S: 1, Z: 1'

    set_summary = puzzle_set.block_summary
    assert set_summary == 'Extras: I: 1(2), JL: 2(1), L: 2(1, 2), O: 1(1), SZ: 2(2)'


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
    set1 = PuzzleSet(puzzle1, puzzle2, puzzle3)
    puzzle_set = set1
    puzzle1, puzzle2, puzzle3 = puzzle_set.puzzles

    summary1 = puzzle1.display_block_summary()
    assert summary1 == 'Block sizes: 4x4, Shapes: O: 4'
    assert puzzle2.display_block_summary() == summary1
    summary3 = puzzle3.display_block_summary()
    assert summary3 == 'Block sizes: 5x4, Shapes: I: 2, J: 1, L: 1, O: 1'

    set_summary = puzzle_set.block_summary
    assert set_summary == 'Extras: I: 2(3), JL: 2(3), O: 1(1, 2, 3)'


def test_shape_counts():
    puzzle_set = parse_puzzle_set()

    shape_counts = puzzle_set.shape_counts

    assert shape_counts == {'I': 1,
                            'J': 2,
                            'L': 2,
                            'O': 1,
                            'S': 1,
                            'Z': 1}


@pytest.mark.skip(reason='Not implemented yet.')
def test_draw_packed(pixmap_differ: PixmapDiffer):
    with pixmap_differ.create_painters(
            180,
            180,
            'test_puzzle_draw_packed') as (actual, expected):
        puzzle_set = parse_puzzle_set()
        puzzle1, puzzle2 = puzzle_set.puzzles
        puzzle1.square_size = 20
        blocks = puzzle1.blocks
        blocks[0].set_display(70, 10, 1)
        # block2.set_display(10, 10, 3)
        # block3.set_display(30, 30, 1)
        for block in puzzle1.blocks:
            block.border_colour = 'blue'
            block.divider_colour = 'red'
            block.draw(expected)

        # puzzle2 = parse_basic_puzzle()
        # packer = BlockPacker(6, 6, tries=1000)
        # packer.fill(Counter('LJI'))
        # puzzle2.draw_packed(actual, packer.positions, square_size=20)
