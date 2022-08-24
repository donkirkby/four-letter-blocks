from io import StringIO
from textwrap import dedent

from PySide6.QtGui import QColor

from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.puzzle import Puzzle
from four_letter_blocks.puzzle_set import PuzzleSet
from tests.pixmap_differ import PixmapDiffer


def parse_puzzle_set(block_packer: BlockPacker = None):
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
    puzzle_set = PuzzleSet(puzzle1, puzzle2, block_packer=block_packer)
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
                            'J': 4,
                            'O': 1,
                            'S': 2}


def test_shape_counts_z_only():
    puzzle_text = dedent("""\
        Title

        ABCDE
        FGHIJ
        KL#MN
        OPQRS
        TUVWX

        -

        AAAAB
        FFFBB
        EF#BD
        ECCDD
        EECCD
    """)
    puzzle1 = Puzzle.parse(StringIO(puzzle_text))
    puzzle2 = Puzzle.parse(StringIO(puzzle_text))
    puzzle_set = PuzzleSet(puzzle1, puzzle2, block_packer=None)

    shape_counts = puzzle_set.shape_counts

    assert shape_counts == {'I': 1,
                            'J': 2,
                            'T': 2,
                            'S': 4}
    block_count = sum(1
                      for shape_blocks in (puzzle_set.front_blocks,
                                           puzzle_set.back_blocks)
                      for blocks in shape_blocks.values()
                      for block in blocks
                      if block is not None)
    assert block_count == 12


def test_draw_packed(pixmap_differ: PixmapDiffer):
    with pixmap_differ.create_painters(
            360,
            180,
            'test_puzzle_draw_packed') as (actual, expected):
        puzzle_set1 = parse_puzzle_set(BlockPacker(10, 10, tries=1000))
        puzzle1, puzzle2 = puzzle_set1.puzzles
        puzzle_set1.square_size = 20
        blocks = puzzle1.blocks
        blocks[0].set_display(270, 10, 0)
        blocks[1].set_display(190, 10, 0)
        blocks[2].set_display(50, 10, 0)
        blocks[3].set_display(70, 70, 0)
        blocks[4].set_display(50, 90, 3)

        blocks = puzzle2.blocks
        blocks[0].set_display(110, 70, 1)
        blocks[1].set_display(130, 10, 0)
        blocks[2].set_display(250, 70, 0)
        blocks[3].set_display(230, 10, 0)
        blocks[4].set_display(210, 90, 1)

        for block in puzzle2.blocks:
            block.face_colour = QColor.fromHsv(120, 30, 255)

        for block in puzzle1.blocks + puzzle2.blocks:
            block.draw(expected, use_text=False)

        puzzle_set2 = parse_puzzle_set(BlockPacker(7, 8, tries=1000))
        puzzle_set2.square_size = 20
        puzzle_set2.draw_front(actual)

        puzzle_set2.draw_back(actual, x_offset=8)
