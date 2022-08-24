from collections import Counter
from textwrap import dedent

import numpy as np

from four_letter_blocks.block_packer import BlockPacker
from tests.pixmap_differ import PixmapDiffer


def test_display():
    state = np.array([[3, 3, 0, 2, 1, 1],
                      [3, 3, 0, 2, 2, 2]])
    expected_display = dedent("""\
        BB.A##
        BB.AAA""")
    display = BlockPacker().display(state)

    assert display == expected_display


def test_empty_display():
    width = 3
    height = 2
    expected_display = dedent("""\
        ...
        ...""")

    display = BlockPacker(width, height).display()

    assert display == expected_display


def test_start_text():
    start = dedent("""\
        BB.A##
        BB.AAA""")
    display = BlockPacker(start_text=start).display()

    assert display == start


def test_fill_one_block():
    width = height = 6
    shape_counts = Counter('I')
    expected_display = dedent("""\
        AAAA..
        ......
        ......
        ......
        ......
        ......""")
    packer = BlockPacker(width, height)
    packer.fill(shape_counts)

    assert packer.display() == expected_display


def test_fill_two_blocks():
    width = height = 5
    shape_counts = Counter('LO')
    expected_display = dedent("""\
        ##ABB
        AAABB
        .....
        .....
        .....""")
    packer = BlockPacker(width, height)
    packer.fill(shape_counts)

    assert packer.display() == expected_display


def test_fill_three_blocks():
    width = height = 5
    shape_counts = Counter('OLO')
    expected_display = dedent("""\
        AABCC
        AABCC
        ..BB.
        .....
        .....""")
    packer = BlockPacker(width, height)
    packer.fill(shape_counts)

    assert packer.display() == expected_display


def test_positions():
    packer = BlockPacker(start_text=dedent("""\
        AA#CC
        AAB.C
        BBB.C
        .....
        ....."""))

    # {shape: [(x, y, rotation)]}
    expected_positions = {'O': [(0, 0, 0)],
                          'L': [(0, 1, 1), (3, 0, 2)]}

    assert packer.positions == expected_positions


def test_flip():
    packer = BlockPacker(start_text=dedent("""\
        AA#CC
        AAB.C
        BBB.C
        ....."""))
    expected_display = dedent("""\
        CC#AA
        C.BAA
        C.BBB
        .....""")

    flipped_packer = packer.flip()

    assert flipped_packer.display() == expected_display


# TODO: Test fill failure.

def test_draw_cuts(pixmap_differ: PixmapDiffer):
    actual, expected = pixmap_differ.start(
        500, 225,
        'test_draw_cuts')

    packer = BlockPacker()
    packer.cell_size = 50
    packer.margin = 5
    packer.nick_radius = 10

    packer.draw_cuts(actual)
    packer.draw_cuts(expected)  # TODO: add real test

    pixmap_differ.assert_equal()
