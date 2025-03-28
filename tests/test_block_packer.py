import re
from collections import Counter
from textwrap import dedent

import numpy as np
import pytest

from four_letter_blocks.block import Block
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


def test_sort_blocks():
    state = np.array([[3, 3, 0, 2, 1, 1],
                      [3, 3, 0, 2, 2, 2]])
    expected_display = dedent("""\
        AA.B##
        AA.BBB""")
    packer = BlockPacker(start_state=state)

    packer.sort_blocks()
    display = packer.display()

    assert display == expected_display


def test_start_text():
    start = dedent("""\
        BB.A##
        BB.AAA""")
    display = BlockPacker(start_text=start).display()

    assert display == start


def test_is_full_true():
    start = dedent("""\
        BBACCC
        BBAAAC""")
    packer = BlockPacker(start_text=start)

    assert packer.is_full


def test_is_full_false():
    start = dedent("""\
        BBA...
        BBAAA.""")
    packer = BlockPacker(start_text=start)

    assert not packer.is_full


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
    width, height = 5, 4
    shape_counts = Counter('LO')
    expected_display = dedent("""\
        AA..B
        AABBB
        .....
        .....""")
    packer = BlockPacker(width, height)
    packer.fill(shape_counts)

    assert packer.display() == expected_display


def test_fill_two_blocks_force_fours():
    width, height = 5, 4
    shape_counts = Counter('LO')
    expected_display = dedent("""\
        AABBB
        AAB..
        .....
        .....""")
    packer = BlockPacker(width, height)
    packer.force_fours = True
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
        AABB.
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
        AABCC
        AABCC
        ..B..
        ..B..
        .....""")
    packer = BlockPacker(width, height)
    packer.fill(shape_counts)

    assert packer.display() == expected_display


def test_no_rotations_needs_gap():
    width = height = 5
    shape_counts = Counter(('O', 'J3', 'O'))
    expected_display = dedent("""\
        AA.CC
        AABCC
        ..BBB
        .....
        .....""")
    packer = BlockPacker(width, height)
    packer.fill(shape_counts)

    assert packer.display() == expected_display


def test_extra_gaps():
    width = height = 5
    shape_counts = Counter({'O': 2, 'S0': 1, 'T0': 2})
    expected_display = dedent("""\
        AAABB
        .A.BB
        .EEE.
        DDECC
        DDCC.""")
    packer = BlockPacker(width, height, tries=100, min_tries=1)
    is_filled = packer.fill(shape_counts)

    assert is_filled
    assert packer.display() == expected_display


def test_random_fill():
    for _ in range(100):
        shape_counts = Counter({'O': 5})
        start_text = dedent("""\
            .##..
            .....
            ..#..
            .....
            ..##.""")
        packer = BlockPacker(start_text=start_text)
        packer.are_slots_shuffled = True
        packer.are_partials_saved = True
        packer.fill(shape_counts)

        assert 1 <= shape_counts['O'] <= 3


def test_random_fill_lower_numbers():
    for _ in range(100):
        shape_counts = Counter({'O': 5})
        start_text = dedent("""\
            .##..
            .....
            ..#..
            ..DDD
            ..##D""")
        packer = BlockPacker(start_text=start_text, tries=100, min_tries=1)
        packer.are_slots_shuffled = True
        packer.are_partials_saved = True
        packer.fill(shape_counts)

        assert 2 <= shape_counts['O'] <= 3
        assert packer.state.max() == 5


def test_random_fill_tries_multiple_shapes():
    for _ in range(100):
        shape_counts = Counter({shape: 1 for shape in Block.shape_names()})
        start_text = dedent("""\
            AA...B
            AA.BBB""")
        packer = BlockPacker(start_text=start_text)
        packer.are_slots_shuffled = True
        packer.are_partials_saved = True
        packer.fill(shape_counts)

        assert shape_counts['L'] == 0


def test_random_fill_no_gaps():
    for _ in range(100):
        shape_counts = Counter({'O': 1})
        packer = BlockPacker(2, 2)
        packer.are_slots_shuffled = True
        packer.are_partials_saved = True
        packer.fill(shape_counts)

        assert shape_counts['O'] == 0
        assert packer.state.max() == 2


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


def test_rotated_positions():
    packer = BlockPacker(start_text=dedent("""\
        AA#CC
        AAB.C
        BBB.C
        .....
        ....."""))

    # {shape: [(x, y)]}
    expected_positions = {'O': [(0, 0)],
                          'L1': [(0, 1)],
                          'L2': [(3, 0)]}

    assert packer.rotated_positions == expected_positions


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


def test_create_blocks_with_gap():
    packer = BlockPacker(start_text=dedent("""\
        AA#DD
        AAB.D
        BBB.D"""))

    blocks = list(packer.create_blocks())

    assert len(blocks) == 3


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
        AA.
        AA.
        BBC
        BBC
        .CC""")
    packer = BlockPacker(width, height, tries=100)
    packer.fill(shape_counts)

    assert packer.display() == expected_display


def test_fill_with_split_row():
    width, height = 3, 7
    shape_counts = Counter('OOT')
    expected_display = dedent("""\
        AA.
        AA.
        ...
        BB.
        BB.
        CCC
        .C.""")
    packer = BlockPacker(width, height, split_row=3, tries=100)
    packer.fill(shape_counts)

    assert packer.display() == expected_display


def test_fill_overflow():
    """ Overflow 8-bit block numbers with 255 blocks. (0 and 1 are blanks.) """
    shape_counts = Counter({'O': 254})

    packer = BlockPacker(256, 4, tries=500)
    packer.fill(shape_counts)

    assert len(packer.positions['O']) == 254

    shape_counts = Counter({'O': 255})
    packer = BlockPacker(256, 4, tries=500)
    with pytest.raises(ValueError, match='Maximum 254 blocks in packer.'):
        packer.fill(shape_counts)


def test_fill_fail():
    shape_counts = Counter({'O': 2})

    packer = BlockPacker(2, 3, tries=500)
    is_filled = packer.fill(shape_counts)

    assert not is_filled


# noinspection DuplicatedCode
def test_place_block():
    packer = BlockPacker(start_text=dedent("""\
        #..#.
        .....
        AA#..
        AA...
        .#..#"""))
    expected_display = dedent("""\
        #..#.
        ...B.
        AA#B.
        AA.BB
        .#..#""")

    states = list(packer.place_block('L0',
                                     1,
                                     3,
                                     3))

    assert len(states) == 1
    assert packer.display(states[0]) == expected_display


# noinspection DuplicatedCode
def test_remove_block():
    packer = BlockPacker(start_text=dedent("""\
        #..#.
        ...B.
        AA#B.
        AA.BB
        .#..#"""))
    expected_display = dedent("""\
        #..#.
        .....
        AA#..
        AA...
        .#..#""")

    shape = packer.remove_block(1, 3)

    assert shape == 'L0'
    assert packer.display() == expected_display


# noinspection DuplicatedCode
def test_remove_block_misses():
    expected_display = dedent("""\
        #..#.
        ...B.
        AA#B.
        AA.BB
        .#..#""")
    packer = BlockPacker(start_text=expected_display)

    with pytest.raises(ValueError, match=re.escape('No block at (1, 2).')):
        packer.remove_block(1, 2)

    assert packer.display() == expected_display


# noinspection DuplicatedCode
def test_find_slots():
    packer = BlockPacker(start_text=dedent("""\
        #..#.
        .....
        ..#..
        .....
        .#..#"""))
    packer.force_fours = True
    # Not at (1, 3) or (2, 0), because they cut off something.
    expected_o_slots = np.array(object=[[0, 1, 0, 0, 0],
                                        [1, 0, 0, 0, 0],
                                        [0, 0, 0, 1, 0],
                                        [0, 0, 1, 0, 0],
                                        [0, 0, 0, 0, 0]],
                                dtype=bool)

    o_slots = packer.find_slots()['O']

    assert np.array_equal(o_slots, expected_o_slots)


def test_find_slots_after_fail():
    packer = BlockPacker(start_text=dedent("""\
        #..#.
        .....
        ..#..
        .....
        .#..#"""))
    packer.fill(Counter({'O': 20}))  # fails

    with pytest.raises(RuntimeError,
                       match='Cannot find slots with invalid state.'):
        packer.find_slots()


def test_find_slots_split_row():
    packer = BlockPacker(start_text=dedent("""\
        #..#.
        .....
        ..#..
        .....
        .#..#"""))
    packer.split_row = 2
    # Not in row 1, because it overlaps the split row.
    expected_o_slots = np.array(object=[[0, 1, 0, 0, 0],
                                        [0, 0, 0, 0, 0],
                                        [1, 0, 0, 1, 0],
                                        [0, 0, 1, 0, 0],
                                        [0, 0, 0, 0, 0]],
                                dtype=bool)

    o_slots = packer.find_slots()['O']

    assert str(o_slots) == str(expected_o_slots)


# noinspection DuplicatedCode
def test_has_slot_coverage():
    packer = BlockPacker(start_text=dedent("""\
        #AA...#
        .AA#.CC
        .....CC
        .#.#.#A
        .....AA
        ..E#BBA
        #EEEBB#"""))
    packer.force_fours = True

    slots = packer.find_slots()

    assert slots


# noinspection DuplicatedCode
def test_has_slot_coverage_fails():
    packer = BlockPacker(start_text=dedent("""\
        #.....#
        .AA#.CC
        .AA..CC
        .#.#.#A
        .....AA
        ..E#BBA
        #EEEBB#"""))
    packer.force_fours = True

    slots = packer.find_slots()

    assert not slots


# noinspection DuplicatedCode
def test_fill_with_extra_blocks():
    packer = BlockPacker(start_text=dedent("""\
        ..
        .."""))

    is_filled = packer.fill(Counter({'O': 2}))

    assert is_filled


def test_shape_counts_7x7():
    packer = BlockPacker(start_text=dedent("""\
        #.....#
        ...#...
        .......
        .#.#.#.
        .......
        ...#...
        #.....#"""))
    expected_shape_counts = {
        name: 3 if name == 'O' else 2 if name[0] in 'ISZ' else 1
        for name in Block.shape_rotation_names()}

    shape_counts = packer.calculate_max_shape_counts()

    assert shape_counts == expected_shape_counts


def test_shape_counts_9x9():
    packer = BlockPacker(start_text=dedent("""\
        .....#...
        .....#...
        .........
        .###....#
        ....#....
        #....###.
        .........
        ...#.....
        ...#....."""))
    expected_shape_counts = {
        name: 4 if name == 'O' else 2 if name[0] in 'ISZ' else 1
        for name in Block.shape_rotation_names()}

    shape_counts = packer.calculate_max_shape_counts()

    assert shape_counts == expected_shape_counts
