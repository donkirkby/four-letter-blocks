from collections import Counter
from textwrap import dedent

from four_letter_blocks.x_packer import XPacker


def test_fill_grid():
    start_text = dedent("""\
        #.....#
        ...#...
        .......
        .#.#.#.
        .......
        ...#...
        #.....#""")
    expected_display = dedent("""\
        #AABBB#
        CAA#GBH
        CEEEGGH
        C#E#G#H
        CDDJJJH
        DDF#JII
        #FFFII#""")
    packer = XPacker(start_text=start_text)
    is_filled = packer.fill()

    assert is_filled
    assert packer.display() == expected_display


def test_fill_tiny_grid():
    start_text = dedent("""\
        #...#
        .....
        .....
        .....
        ##..#""")
    expected_display = dedent("""\
        #CBB#
        CCEBB
        CEEEA
        DDDAA
        ##DA#""")
    packer = XPacker(start_text=start_text)
    is_filled = packer.fill()

    assert is_filled
    assert packer.display() == expected_display


def test_fill_big_grid():
    start_text = dedent("""\
        .#...........#.
        ...##.....##...
        ....#.....#....
        .....#...#.....
        .##....#....##.
        #.............#
        ...#...#...#...
        ....#.###.#....
        ...#...#...#...
        #.............#
        .##....#....##.
        .....#...#.....
        ....#.....#....
        ...##.....##...
        .#...........#.""")
    expected_display = dedent("""\
        A#EEQQQQjHHHH#C
        AEE##hhijj##GGC
        AAFF#hhikj#GGCC
        BBBFV#iik#nnDDD
        B##FVVV#klnn##D
        #UUUUXXXklmmmY#
        RRT#WWX#llm#[YY
        RRTT#W###`#[[ZY
        SST#cWa#``]#[ZZ
        #SScccaaa`]]]Z#
        J##bbdd#^^^P##N
        JJJbb#dgg#^PNNN
        IIKK#edgff#PPMM
        IKK##eegff##OOM
        I#LLLLe____OO#M""")
    packer = XPacker(start_text=start_text)
    is_filled = packer.fill()

    assert is_filled
    assert packer.display() == expected_display


def test_fill_slow_grid():
    """ This grid takes almost a minute to solve as is, but well under a second
    if you shuffle the options and get lucky.
    """
    start_text = dedent("""\
        ......#....##
        ....#....#.##
        ....#......##
        .#........###
        ...###.##.###
        .....#.....##
        #.##.###...##
        #........#.##
        ......#....##
        .#....#....##
        ....#......##
        #############
        ....#...#....
        ...#....#....
        .....AA.#....
        #....AA.....#
        ....#....#...
        .....#....##.
        ......#......
        .##....#.....
        ...#....#....
        #...........#
        ....#........
        ....#....#...
        ....#...#....""")
    packer = XPacker(start_text=start_text)
    packer.retries = 10
    packer.timeout = 1
    is_filled = packer.fill()

    assert is_filled


def test_fill_travel_grid():
    start_text = dedent("""\
        .....
        .....
        .....
        .....
        .....""")
    expected_display = dedent("""\
        AABB#
        #AABB
        CC#D#
        #CCD#
        ##DD#""")
    packer = XPacker(start_text=start_text)
    packer.target_shape_counts = Counter({'J0': 1, 'Z0': 3})
    packer.force_fours = False
    is_filled = packer.fill()

    assert is_filled
    assert packer.display() == expected_display


def test_format_dlx():
    start_text = dedent("""\
        #...#
        .....
        ..#..
        .....
        #...#""")
    expected_dlx_start = dedent("""\
        0_1 0_2 0_3 1_0 1_1 1_2 1_3 1_4 2_0 2_1 2_3 2_4 3_0 3_1 \
3_2 3_3 3_4 4_1 4_2 4_3
        0_1 0_2 1_0 1_1
        0_1 0_2 1_1 2_1""")
    packer = XPacker(start_text=start_text)

    dlx_text = packer.format_dlx(sorted_options=True)

    dlx_start = dlx_text[:len(expected_dlx_start)]
    assert dlx_start == expected_dlx_start
