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
        #DDE#
        DDBEE
        CCBEA
        CCBAA
        ##BA#""")
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
        BBBFV#iik#mmDDD
        B##FVVV#klmm##D
        #UUUUXXXklnnnY#
        RRT#WWX#lln#[YY
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


def test_format_dlx():
    start_text = dedent("""\
        #...#
        .....
        ..#..
        .....
        #...#""")
    expected_dlx_start = dedent("""\
        s0_1 s0_2 s0_3 s1_0 s1_1 s1_2 s1_3 s1_4 s2_0 s2_1 s2_3 s2_4 s3_0 s3_1 \
s3_2 s3_3 s3_4 s4_1 s4_2 s4_3 I:10;5 J:10;5 L:10;5 O:10;5 S:10;5 T:10;5 Z:10;5
        L s2_1 s3_1 s4_1 s4_2
        L s2_4 s3_2 s3_3 s3_4""")
    packer = XPacker(start_text=start_text)

    dlx_text = packer.format_dlx(sorted_options=True)

    dlx_start = dlx_text[:len(expected_dlx_start)]
    assert dlx_start == expected_dlx_start
