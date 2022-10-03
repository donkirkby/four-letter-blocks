from collections import Counter
from textwrap import dedent

import numpy as np
import pytest

from four_letter_blocks.block_packer import BlockPacker


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


def test_display_max_ascii():
    shape_counts = Counter({'O': 62})
    expected_display_end = dedent("""\
        }}
        }}
        ~~
        ~~""")

    packer = BlockPacker(2, 124, tries=500)
    packer.fill(shape_counts)

    display = packer.display()
    display_lines = display.splitlines()
    display_end = '\n'.join(display_lines[-4:])

    assert display_end == expected_display_end


def test_display_beyond_ascii():
    shape_counts = Counter({'O': 63})

    packer = BlockPacker(2, 126, tries=500)
    packer.fill(shape_counts)

    with pytest.raises(RuntimeError, match='Too many blocks for text display'):
        packer.display()


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
    is_filled = packer.fill(shape_counts)

    assert packer.display() == expected_display
    assert is_filled


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


def test_fill_no_shapes():
    width = height = 5
    shape_counts = Counter()
    expected_display = dedent("""\
        .....
        .....
        .....
        .....
        .....""")
    packer = BlockPacker(width, height)
    is_filled = packer.fill(shape_counts)

    assert packer.display() == expected_display
    assert is_filled


def test_fill_three_blocks():
    width = height = 5
    shape_counts = Counter('OLO')
    expected_display = dedent("""\
        AABB#
        AABBC
        ..CCC
        .....
        .....""")
    packer = BlockPacker(width, height)
    packer.fill(shape_counts)

    assert packer.display() == expected_display


def test_no_rotations():
    width = height = 5
    shape_counts = Counter(('O', 'I0', 'O'))
    expected_display = dedent("""\
        AABBC
        AABBC
        ....C
        ....C
        .....""")
    packer = BlockPacker(width, height)
    packer.fill(shape_counts)

    assert packer.display() == expected_display


def test_no_rotations_needs_gap():
    width = height = 5
    shape_counts = Counter(('O', 'J3', 'O'))
    expected_display = dedent("""\
        AA#BB
        AACBB
        ..CCC
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


def test_create_blocks():
    packer = BlockPacker(start_text=dedent("""\
        AA#CC
        AAB.C
        BBB.C"""))

    a, b, c = packer.create_blocks()

    assert (a.x, a.y) == (0, 0)
    assert (b.x, b.y) == (0, 1)
    assert (c.x, c.y) == (3, 0)
    assert a.shape == 'O'
    assert b.shape == 'L'


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


def test_fill_with_underhang():
    width, height = 3, 5
    shape_counts = Counter('OOJ')
    expected_display = dedent("""\
        AAB
        AAB
        #BB
        CC.
        CC.""")
    packer = BlockPacker(width, height, tries=100)
    packer.fill(shape_counts)

    assert packer.display() == expected_display


def test_fill_overflow():
    """ Overflow 8-bit block numbers with 255 blocks. (0 and 1 are blanks.) """
    shape_counts = Counter({'O': 254})

    packer = BlockPacker(256, 4, tries=500)
    packer.fill(shape_counts)

    assert len(packer.positions['O']) == 254

    shape_counts['O'] += 1
    packer = BlockPacker(256, 4, tries=500)
    with pytest.raises(ValueError, match='Maximum 254 blocks in packer.'):
        packer.fill(shape_counts)


def test_fill_fail():
    shape_counts = Counter({'O': 2})

    packer = BlockPacker(2, 3, tries=500)
    is_filled = packer.fill(shape_counts)

    assert not is_filled
