from collections import Counter
from textwrap import dedent

from four_letter_blocks.x_packer import XPacker


def test_fill_grid():
    shape_counts = Counter('I')
    start_text = dedent("""\
        #...#
        .....
        ..#..
        .....
        #...#""")
    expected_display = dedent("""\
        #AEE#
        AAEED
        BA#DD
        BBBCD
        #CCC#""")
    packer = XPacker(start_text=start_text)
    packer.required_shape_counts = shape_counts
    is_filled = packer.fill()

    assert packer.display() == expected_display
    assert is_filled


def test_fill_big_grid():
    shape_counts = Counter('I')
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
        A#CDDDDaaaOOO#L
        AAC##````a##OLL
        ACCE#___bb#NNNL
        BBBEE#]_b#WNMMM
        B##E]]]#bWWW##M
        #ZX[[[^^ccdddj#
        ZZX#[^^#ccd#hjj
        YZXX#T###e#hhij
        YYY#TTT#Vee#hii
        #SSSRRVVVegggi#
        K##SRUU#fffg##G
        KKQQR#UUk#fHGGG
        JKQQ#lkkkm#HHHF
        JJP##llmmm##IFF
        J#PPPlnnnnIII#F""")
    packer = XPacker(start_text=start_text)
    packer.required_shape_counts = shape_counts
    is_filled = packer.fill()

    assert is_filled
    assert packer.display() == expected_display
