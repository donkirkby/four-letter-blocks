from textwrap import dedent

import numpy as np
import pytest

from four_letter_blocks.double_block_packer import DoubleBlockPacker


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


def test_group_start_texts():
    # 40 spaces
    start_text7x7 = dedent("""\
        #.....#
        ...#...
        .......
        .#.#.#.
        .......
        ...#...
        #.....#""")

    # 96 spaces
    start_text11x11 = dedent("""\
        #....#.....
        .....#...#.
        .........#.
        .##.##.....
        .#.....#...
        #....#....#
        ...#.....#.
        .....##.##.
        .#.........
        .#....#....
        ......#...#""")

    # 144 spaces
    start_text13x13 = dedent("""\
        ......#......
        ....#........
        ......#......
        .##....#.....
        .....#....##.
        ...#....#....
        #.....#.....#
        ....#....#...
        .##....#.....
        .....#....##.
        .......#.....
        .........#...
        .......#.....""")

    # 200 spaces
    start_text15x15 = dedent("""\
        ......#........
        ......#........
        ......#........
        ...#...#.......
        ....#.....#....
        .........#.....
        ........#......
        ###....#....###
        ......#........
        .....#.........
        ....#.....#....
        .......#...#...
        ........#......
        ........#......
        ........#......""")

    expected_display = dedent("""\
        #.....#########
        ...#...########
        .......########
        .#.#.#.########
        .......########
        ...#...########
        #.....#########
        ###############
        ......#........
        ......#........
        ......#........
        ...#...#.......
        ....#.....#....
        .........#.....
        ........#......
        ###....#....###
        ......#........
        .....#.........
        ....#.....#....
        .......#...#...
        ........#......
        ........#......
        ........#......

        #....#.....####
        .....#...#.####
        .........#.####
        .##.##.....####
        .#.....#...####
        #....#....#####
        ...#.....#.####
        .....##.##.####
        .#.........####
        .#....#....####
        ......#...#####
        ###############
        ......#......##
        ....#........##
        ......#......##
        .##....#.....##
        .....#....##.##
        ...#....#....##
        #.....#.....###
        ....#....#...##
        .##....#.....##
        .....#....##.##
        .......#.....##
        .........#...##
        .......#.....##""")

    packer = DoubleBlockPacker(start_text7x7,
                               start_text11x11,
                               start_text13x13,
                               start_text15x15)

    assert packer.display() == expected_display
