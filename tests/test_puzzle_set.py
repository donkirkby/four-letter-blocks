from io import StringIO
from textwrap import dedent

import pytest
from PySide6.QtGui import QPainter, QPixmap

from four_letter_blocks.block import Block
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.puzzle import Puzzle
from four_letter_blocks.puzzle_set import PuzzleSet
from four_letter_blocks import four_letter_blocks_rc
from tests.pixmap_differ import PixmapDiffer

assert four_letter_blocks_rc  # Need to import this module to load resources.


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
    assert set_summary == '10 blocks with extras: I: 1(2), JL: 2(1), L: 2, O: 1(1), SZ: 2(2)'


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
    assert set_summary == '13 blocks with extras: I: 2(3), JL: 2(3), O: 1'


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

    set_summary = puzzle_set.block_summary
    assert set_summary == '8 blocks'


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


def test_draw_background(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(360, 180) as (actual, expected):
        full_tile = QPixmap(':/light-wood-texture.jpg')
        tile = full_tile.copy(0, 0, 100, 100)
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
        puzzle_set1 = parse_puzzle_set(BlockPacker(10, 10, tries=1000))
        puzzle1, puzzle2 = puzzle_set1.puzzles
        puzzle_set1.square_size = 20
        blocks = puzzle1.blocks
        blocks[0].set_display(270, 10, 0)
        blocks[1].set_display(170, 10, 2)
        blocks[2].set_display(50, 10, 1)
        blocks[3].set_display(10, 70, 0)
        blocks[4].set_display(50, 70, 3)

        blocks = puzzle2.blocks
        blocks[0].set_display(90, 50, 1)
        blocks[1].set_display(130, 30, 0)
        blocks[2].set_display(230, 30, 1)
        blocks[3].set_display(210, 70, 1)
        blocks[4].set_display(210, 10, 3)

        for block in puzzle1.blocks + puzzle2.blocks:
            block.draw(expected, is_packed=True)

        puzzle_set2 = parse_puzzle_set(BlockPacker(7, 8, tries=1000))
        puzzle_set2.square_size = 20
        puzzle_set2.draw_front(actual)

        actual.setViewport(160, 0, 360, 180)
        puzzle_set2.draw_back(actual)


def test_draw_cuts(pixmap_differ: PixmapDiffer):
    with pixmap_differ.create_painters(
            360,
            180,
            'test_puzzle_draw_cuts') as (actual, expected):
        block_text = dedent("""\
            #ABBBCC
            #AD#BCE
            AADDFCE
            GGHDFFE
            GGHHHFE
        """)
        puzzle3 = Puzzle.parse_sections('',
                                        block_text,
                                        '',
                                        block_text)
        puzzle3.square_size = 20
        for block in puzzle3.blocks:
            block.x += 10
            block.y += 10
            block.border_colour = Block.CUT_COLOUR
            block.draw_outline(expected)

        puzzle_set = parse_puzzle_set(BlockPacker(7, 8, tries=1000))
        puzzle_set.square_size = 20
        puzzle_set.draw_cuts(actual)


@pytest.mark.parametrize(
    'sizes, expected',
    # Standard sizes in order
    (((7, 9, 11, 13, 15), ((120, 60), (0, 0), (60, 60), (30, 60), (0, 60))),
     # Standard sizes out of order
     ((9, 7, 11, 13, 15), ((0, 0), (120, 60), (60, 60), (30, 60), (0, 60))),
     # Some standard sizes
     ((9, 11, 13, 15), ((0, 0), (60, 60), (30, 60), (0, 60))),
     # Nonstandard sizes
     ((9, 10, 11, 12), ((0, 0), (240, 60), (120, 60), (0, 60))),
     # Repeated sizes
     ((9, 9), ((0, 0), (0, 60)))))
def test_colours(sizes, expected):
    puzzles = []
    for size in sizes:
        grid_text = '\n'.join(['X'*size]*size)
        puzzle = Puzzle.parse_sections(f'{size=}',
                                       grid_text,
                                       '',
                                       '')
        puzzles.append(puzzle)

    PuzzleSet(*puzzles, block_packer=BlockPacker(20, 20, tries=1000))

    colours = (puzzle.face_colour for puzzle in puzzles)
    colour_params = tuple((colour.hue(), colour.saturation())
                          for colour in colours)
    assert colour_params == expected
