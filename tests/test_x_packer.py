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
