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
        #.....#
        #..#..#
        #.....#
        ...#...
        #.....#""")
    with pytest.raises(ValueError, match=r'Different space counts: 40 and 36\.'):
        DoubleBlockPacker(front_text, back_text)


def test_fill():
    expected_display = dedent("""\
        ABB#CCCCD
        ABB#EEFFD
        AAG#EFFDD
        GGGHEIIII
        ###H#J###
        KKHHJJLLL
        KMMMJ#LNN
        KOMPP#QQN
        OOOPP#QQN
        
        BBA#GCCCC
        BBA#GGGPP
        DAA#MMMPP
        DIIIIM###
        DDEE#FFKK
        ###ENNFFK
        LLLEN#HJK
        QQLON#HJJ
        QQOOO#HHJ""")
    front_text = dedent("""\
        ...#.....
        ...#.....
        ...#.....
        .........
        ###.#.###
        .........
        .....#...
        .....#...
        .....#...""")
    back_text = dedent("""\
        ...#.....
        ...#.....
        ...#.....
        ......###
        ....#....
        ###......
        .....#...
        .....#...
        .....#...""")
    packer = DoubleBlockPacker(front_text, back_text)
    is_filled = packer.fill()

    assert is_filled
    packer.sort_blocks()

    assert packer.display() == expected_display


def test_tiny_fill():
    expected_display = dedent("""\
        #AAB#
        AACBB
        DCCCB
        DDEEE
        #D#E#

        #B#C#
        BBCCC
        BEEED
        AAEDD
        #AAD#""")
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


def test_already_filled():
    front_text = dedent("""\
        #ABB#
        AAABB
        DDDDC
        EEECC
        #E#C#""")
    back_text = dedent("""\
        #A#C#
        AAACC
        EEEEC
        DDDBB
        #DBB#""")
    expected_display = dedent("""\
        #ABB#
        AAABB
        DDDDC
        EEECC
        #E#C#

        #A#C#
        AAACC
        EEEEC
        DDDBB
        #DBB#""")
    packer = DoubleBlockPacker(front_text, back_text)
    is_filled = packer.fill()

    assert is_filled
    assert packer.display() == expected_display


def xtest_interactive():
    front_text = dedent("""\
         #.....#
         ...#...
         .......
         .#.#.#.
         .......
         ...#...
         #.....#""")
    back_text = dedent("""\
         ....#.#
         .......
         ....#.#
         ...#...
         #.#....
         .......
         #.#....""")
    packer = DoubleBlockPacker(front_text, back_text)
    is_filled = packer.fill()

    assert is_filled
    print()
    print(packer.display())


def test_state():
    front_text = dedent("""\
        AAAC
        ABCC
        BBDC
        BDDD
        """)
    back_text = dedent("""\
        CAAA
        CCBA
        CDBB
        DDDB""")
    expected_state = np.array([[2, 2, 2, 4],
                               [2, 3, 4, 4],
                               [3, 3, 5, 4],
                               [3, 5, 5, 5],
                               [4, 2, 2, 2],
                               [4, 4, 3, 2],
                               [4, 5, 3, 3],
                               [5, 5, 5, 3]])

    packer = DoubleBlockPacker(front_text, back_text)

    double_state = packer.state

    np.testing.assert_array_equal(double_state, expected_state)


# noinspection DuplicatedCode
def test_display():
    packer = DoubleBlockPacker(
        dedent("""\
            #.A#B
            ..ABB
            .AAB.
            .....
            #.#.#"""),
        dedent("""\
            #.#.#
            .....
            B.A..
            BBA..
            #BAA#"""))
    expected_display = dedent("""\
        #.A#B
        ..ABB
        .AAB.
        .....
        #.#.#

        #.#.#
        .....
        B.A..
        BBA..
        #BAA#""")

    assert packer.display() == expected_display


def test_sort_blocks():
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
        .......
        #.....#
        ...#...
        #.....#
        .......
        #.....#""")

    expected_display = dedent("""\
        #AAABB#
        CCA#DBB
        ECCDDFF
        E#G#D#F
        EEGGHHF
        IIG#JHH
        #IIJJJ#

        #BBCCJ#
        BBCCJJJ
        #GFFED#
        GGF#EDD
        #GFEED#
        AAAHHII
        #AHHII#""")

    packer = DoubleBlockPacker(front_text, back_text)

    is_filled = packer.fill()
    assert is_filled
    packer.sort_blocks()

    assert packer.display() == expected_display


def test_validate_good():
    front_text = dedent("""\
        #ABB#
        AAABB
        .....
        .....
        #.#.#""")
    back_text = dedent("""\
        #A#.#
        AAA..
        .....
        ...BB
        #.BB#""")

    # No exception.
    DoubleBlockPacker(front_text, back_text)


def test_validate_shapes():
    front_text = dedent("""\
        #ABB#
        AAABB
        .....
        .....
        #.#.#""")
    back_text = dedent("""\
        #A#.#
        AAA..
        B....
        BB...
        #B..#""")

    expected_error = r'Missing shape S0 in back, shape Z1 in front\.'
    with pytest.raises(ValueError, match=expected_error):
        DoubleBlockPacker(front_text, back_text)


def test_validate_block_sizes():
    front_text = dedent("""\
        #ABB#
        AAAB.
        .....
        .....
        #.#.#""")
    back_text = dedent("""\
        #A#.#
        AAA..
        BA...
        BB...
        #B..#""")

    expected_error = r'Bad block size for A in back, B in front\.'
    with pytest.raises(ValueError, match=expected_error):
        DoubleBlockPacker(front_text, back_text)


def test_validate_gap_sizes():
    front_text = dedent("""\
        #B..#
        BB...
        AB...
        AA...
        #A#.#""")
    back_text = dedent("""\
        #.#.#
        ..B..
        ..BBA
        ..BAA
        #..A#""")

    expected_error = r'Bad unused sizes of 3 in back, 9 in back\.'
    with pytest.raises(ValueError, match=expected_error):
        DoubleBlockPacker(front_text, back_text)


def test_validate_unsolvable():
    front_text = dedent("""\
        #...#
        ...AA
        .BAA.
        .BB..
        #B#.#""")
    back_text = dedent("""\
        #.#.#
        ..B..
        ..BB.
        ..BAA
        #.AA#""")

    expected_error = r'Fill failed in front\.'
    with pytest.raises(ValueError, match=expected_error):
        DoubleBlockPacker(front_text, back_text)


def test_validate_warnings():
    front_text = dedent("""\
        #AAA#
        ..A..
        .....
        .....
        #.#.#""")
    back_text = dedent("""\
        #.#.#
        .....
        .....
        ..AAA
        #..A#""")

    expected_error = (r'Found complete word on one block from \(2, 1\) to '
                      r'\(4, 1\) in front\.')
    with pytest.raises(ValueError, match=expected_error):
        DoubleBlockPacker(front_text, back_text)


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
