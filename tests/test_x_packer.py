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
        #AACCC#
        BAA#CJJ
        BBFFJJI
        B#F#G#I
        DDFGGII
        DDE#GHH
        #EEEHH#""")
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
        A#CCEEEE]IIII#F
        ACC##ZZ[]]##HHF
        AADD#ZZ[^]#HHFF
        BBBDS#[[^#__GGG
        B##DSSS#^^__##G
        #TWWWffeedddbb#
        TTV#Wff#eed#`bb
        TUVV#g###j#```a
        UUV#Xgh#ijj#caa
        #UXXXghiiijcca#
        K##YYgh#kkkc##O
        KKKYY#hmk#QQOOO
        JJLL#nmmll#QQNN
        JLL##nnmll##PPN
        J#MMMMnRRRRPP#N""")
    packer = XPacker(start_text=start_text)
    is_filled = packer.fill()

    assert is_filled
    assert packer.display() == expected_display
