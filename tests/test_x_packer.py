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
        #AAABB#
        GGA#BBC
        HGGFFCC
        H#J#F#C
        HHJJFDD
        IIJ#EDD
        #IIEEE#""")
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
        A#EEVVVVaHHHH#C
        AEE##__`aa##GGC
        AAFF#__`ba#GGCC
        BBBFU#``b#[[DDD
        B##FUUU#bb[[##D
        #QTTTddcc]]]XX#
        QQS#Tdd#cc]#YXX
        QRSS#h###k#YYYW
        RRS#fhi#jkk#ZWW
        #RfffhijjjkZZW#
        J##eehi#lllZ##N
        JJJee#iml#PPNNN
        IIKK#nmmgg#PPMM
        IKK##nnmgg##OOM
        I#LLLLn^^^^OO#M""")
    packer = XPacker(start_text=start_text)
    is_filled = packer.fill()

    assert is_filled
    assert packer.display() == expected_display
