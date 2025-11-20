from collections import Counter
from datetime import datetime
from textwrap import dedent

import numpy as np
import pytest

from four_letter_blocks.double_block_packer import DoubleBlockPacker
from four_letter_blocks.x_packer import XPacker


def test_different_space_count():
    front_text = dedent("""\
        #.....#
        ...#...
        .......
        .#.#.#.
        .......
        ...#...
        #.....#""")
    back_text = dedent("""\
        #.....#
        ...#...
        ......#
        ##.#.##
        #......
        ...#...
        #.....#""")
    with pytest.raises(ValueError, match=r'Different space counts: 40 and 36\.'):
        DoubleBlockPacker(front_text, back_text)


def test_fill():
    expected_display = dedent("""\
        AAB#CCCDD
        AAB#CEEDD
        FBB#GHEEI
        FFFGGHIII
        ###G#H###
        JJJKKHLLL
        MJNNK#OOL
        MNNPK#OQQ
        MMPPP#OQQ
        
        AAH#NNJJJ
        AAH#MNNJF
        KKH#MBFFF
        KIHMMB###
        KIII#BBDD
        ###GCCCDD
        LLLGG#COO
        LEEPG#QQO
        EEPPP#QQO""")
    front_text = dedent("""\
        ...#.....
        ...#.....
        ...#.....
        .........
        ###.#.###
        ...BB....
        ....B#...
        ....B#.AA
        .....#.AA""")
    back_text = dedent("""\
        AA.#.....
        AA.#.....
        BB.#.....
        B.....###
        B...#....
        ###......
        .....#...
        .....#...
        .....#...""")
    packer = DoubleBlockPacker(front_text, back_text)
    is_filled = packer.fill()

    assert is_filled
    packer.sort_blocks()

    assert packer.display() == expected_display

# TODO: Fill front within ranges, then fill back with specific counts.
# TODO: Reproduce interference between multiple solvers.
# TODO: Launch back solver through command-line interface.

def test_tiny_fill():
    expected_display = dedent("""\
        #ABB#
        AAABB
        CCCCD
        EEEDD
        #E#D#

        #A#D#
        AAADD
        CCCCD
        EEEBB
        #EBB#""")
    front_text = dedent("""\
        #...#
        .....
        .....
        .....
        #.#.#""")
    back_text = dedent("""\
        #.#.#
        .....
        .....
        .....
        #...#""")
    packer = DoubleBlockPacker(front_text, back_text)
    is_filled = packer.fill()

    assert is_filled
    packer.sort_blocks()

    assert packer.display() == expected_display


def test_state():
    front_text = dedent("""\
        AAA
        A#B
        BBB""")
    back_text = dedent("""\
        AAB
        A#B
        ABB""")
    expected_state = np.array([[2, 2, 2],
                               [2, 1, 3],
                               [3, 3, 3],
                               [2, 2, 3],
                               [2, 1, 3],
                               [2, 3, 3]])

    packer = DoubleBlockPacker(front_text, back_text)

    double_state = packer.state

    np.testing.assert_array_equal(double_state, expected_state)


# noinspection DuplicatedCode
def test_display():
    packer = DoubleBlockPacker(
        dedent("""\
            #..#.
            ...B.
            AA#B.
            AA.BB
            .#..#"""),
        dedent("""\
            #AA.#
            .AA..
            ..#B.
            ...B.
            #.BB#"""))
    expected_display = dedent("""\
        #..#.
        ...B.
        AA#B.
        AA.BB
        .#..#

        #AA.#
        .AA..
        ..#B.
        ...B.
        #.BB#""")

    assert packer.display() == expected_display


def test_sort_blocks():
    front_text = dedent("""\
        #AAAAB#
        CDD#BBE
        CDDFFBE
        C#G#F#E
        CGGGFHE
        III#HHH
        #IJJJJ#""")
    back_text = dedent("""\
        AAAABB#
        C#D#BEE
        CDDDBEE
        C#F#G#H
        CFFFGGH
        III#G#H
        #IJJJJH""")

    expected_display = dedent("""\
        #AAAAB#
        CDD#BBE
        CDDFFBE
        C#G#F#E
        CGGGFHE
        III#HHH
        #IJJJJ#
        
        AAAAFF#
        C#G#FDD
        CGGGFDD
        C#H#B#E
        CHHHBBE
        III#B#E
        #IJJJJE""")

    packer = DoubleBlockPacker(front_text, back_text)

    packer.sort_blocks()

    assert packer.display() == expected_display


def xtest_group_fill():
    start_text9x9 = dedent("""\
        .....#...
        .....#...
        .........
        .###....#
        ....#....
        #....###.
        .........
        ...#.....
        ...#.....""")

    start_text11x11 = dedent("""\
        ....#......
        ...#...#...
        ....#......
        ...........
        .##...#...#
        .....#.....
        #...#...##.
        ...........
        ......#....
        ...#...#...
        ......#....""")

    start_text13x13 = dedent("""\
        ....#...#....
        ....#...#....
        ....#...#....
        ....#......##
        .........#...
        ###....#.....
        ......#......
        .....#....###
        ...#.........
        ##......#....
        ....#...#....
        ....#...#....
        ....#...#....""")

    start_text11x11b = dedent("""\
        ......#....
        ...#.......
        ......#....
        .......#...
        .##...#...#
        .....#.....
        #...#...##.
        ...#.......
        ....#......
        .......#...
        ....#......""")

    packer = DoubleBlockPacker(start_text9x9,
                               start_text11x11,
                               start_text13x13,
                               start_text11x11b)
    packer.filter_seconds = 60
    packer.filter_limit = 150

    # assert packer.display() == expected_display
    is_filled = packer.fill()
    assert is_filled


def xtest_group_enumerate():
    start_text9x9 = dedent("""\
        .....#...
        .....#...
        .........
        .###....#
        ....#....
        #....###.
        .........
        ...#.....
        ...#.....""")

    start_text11x11 = dedent("""\
        ....#......
        ...#...#...
        ....#......
        ...........
        .##...#...#
        .....#.....
        #...#...##.
        ...........
        ......#....
        ...#...#...
        ......#....""")

    start_text13x13 = dedent("""\
        ....#...#....
        ....#...#....
        ....#...#....
        ....#......##
        .........#...
        ###....#.....
        ......#......
        .....#....###
        ...#.........
        ##......#....
        ....#...#....
        ....#...#....
        ....#...#....""")

    start_text11x11b = dedent("""\
        ......#....
        ...#.......
        ......#....
        .......#...
        .##...#...#
        .....#.....
        #...#...##.
        ...#.......
        ....#......
        .......#...
        ....#......""")

    packer = DoubleBlockPacker(start_text9x9,
                               start_text11x11,
                               start_text13x13,
                               start_text11x11b)

    # assert packer.display() == expected_display
    for i, _ in enumerate(packer.front_packer.find_fillings(yield_states=False)):
        index_text = str(i)
        digit_counts = Counter(index_text)
        if digit_counts['0'] == len(index_text) - 1:
            timestamp = datetime.now()
            print(timestamp, i)
    assert 1 == 0
    # is_filled = packer.fill()
    # assert is_filled


def xtest_group_enumerate_unique():
    start_text9x9 = dedent("""\
        .....#...
        .....#...
        .........
        .###....#
        ....#....
        #....###.
        .........
        ...#.....
        ...#.....""")

    start_text11x11 = dedent("""\
        ....#......
        ...#...#...
        ....#......
        ...........
        .##...#...#
        .....#.....
        #...#...##.
        ...........
        ......#....
        ...#...#...
        ......#....""")

    start_text13x13 = dedent("""\
        ....#...#....
        ....#...#....
        ....#...#....
        ....#......##
        .........#...
        ###....#.....
        ......#......
        .....#....###
        ...#.........
        ##......#....
        ....#...#....
        ....#...#....
        ....#...#....""")

    start_text11x11b = dedent("""\
        ......#....
        ...#.......
        ......#....
        .......#...
        .##...#...#
        .....#.....
        #...#...##.
        ...#.......
        ....#......
        .......#...
        ....#......""")

    packer = DoubleBlockPacker(start_text9x9,
                               start_text11x11,
                               start_text13x13,
                               start_text11x11b)

    # assert packer.display() == expected_display
    found_combinations = set()
    display_packer = XPacker(packer.width, packer.height)
    display_packer.target_shape_counts = Counter({'L1': 1})
    for i, state in enumerate(packer.front_packer.find_fillings()):
        display_packer.state = state
        shape_counts = display_packer.packed_shape_counts
        shape_counts_text = ', '.join(
            f'{shape}: {n}' for shape, n in sorted(shape_counts.items()))
        found_combinations.add(shape_counts_text)
        index_text = str(i)
        digit_counts = Counter(index_text)
        if digit_counts['0'] == len(index_text) - 1:
            found_count = len(found_combinations)
            timestamp = datetime.now()
            print(timestamp, i, found_count, round(found_count / i * 100))
    assert 1 == 0
    # is_filled = packer.fill()
    # assert is_filled
