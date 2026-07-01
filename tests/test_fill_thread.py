from textwrap import dedent

from four_letter_blocks.double_block_packer import DoubleBlockPacker
from four_letter_blocks.fill_thread import FillThread
from four_letter_blocks.x_packer import XPacker


def test_source_and_target_init():
    target_text = dedent('''\
        .....
        .....
        .....
        .....
        .....''')
    source_text = dedent('''\
        #AAA#
        EABBB
        EE#BC
        EDDCC
        #DDC#''')
    expected_shape_targets = {'J1': 1, 'T0': 1, 'S1': 1, 'O': 1, 'T3': 1}

    thread = FillThread([target_text], [source_text])

    assert isinstance(thread.packer, XPacker)
    assert thread.packer.target_shape_counts == expected_shape_targets


def test_source_and_target_run():
    target_text = dedent('''\
        .....
        .....
        .....
        .....
        .....''')
    source_text = dedent('''\
        #AAA#
        EABBB
        EE#BC
        EDDCC
        #DDC#''')
    expected_target_text = dedent('''\
        CCC#D
        #C#DD
        BBBED
        AABEE
        AA##E''')
    thread = FillThread([target_text], [source_text])

    thread.run()
    assert thread.progress is not None
    assert thread.progress.is_success
    assert thread.progress.target_texts == (expected_target_text,)


def test_source_and_target_partly_filled():
    target_text = dedent('''\
        .....
        CCC.D
        AC.DD
        AABBD
        .ABB.''')
    source_text = dedent('''\
        #AAA#
        EABBB
        EE#BC
        EDDCC
        #DDC#''')
    expected_shape_targets = {'J1': 1}

    thread = FillThread([target_text], [source_text])

    assert isinstance(thread.packer, XPacker)
    assert thread.packer.target_shape_counts == expected_shape_targets


def test_source_and_target_partly_filled_run():
    target_text = dedent('''\
        .....
        CCC.D
        AC.DD
        AABBD
        .ABB.''')
    source_text = dedent('''\
        #AAA#
        EABBB
        EE#BC
        EDDCC
        #DDC#''')
    expected_target_text = dedent('''\
        #EEE#
        CCCED
        AC#DD
        AABBD
        #ABB#''')

    thread = FillThread([target_text], [source_text])

    thread.run()
    assert thread.progress is not None
    assert thread.progress.is_success
    assert thread.progress.target_texts == (expected_target_text,)


def test_front_and_back_init():
    front_target_text = dedent('''\
        ....#.#
        .......
        ....#.#
        ...#...
        #.#....
        .......
        #.#....''')
    back_target_text = dedent('''\
        #.....#
        ...#...
        .......
        .#.#.#.
        .......
        ...#...
        #.....#''')

    thread = FillThread([front_target_text, back_target_text])

    assert isinstance(thread.packer, DoubleBlockPacker)
    assert thread.packer.front_text == front_target_text
    assert thread.packer.back_text == back_target_text

def test_front_and_back_run():
    front_target_text = dedent('''\
        ....#.#
        .......
        ....#.#
        ...#...
        #.#....
        .......
        #.#....
    ''')
    back_target_text = dedent('''\
        #.....#
        ...#...
        .......
        .#.#.#.
        .......
        ...#...
        #.....#
    ''')
    expected_front_text = dedent('''\
        HHCC#A#
        GHHCCAA
        GFFF#A#
        GGF#EDD
        #B#EEED
        BBIIJJD
        #B#IIJJ''')
    expected_back_text = dedent('''\
        #CCFFF#
        CCB#FHH
        DDBBHHG
        D#B#A#G
        DIIAAGG
        IIE#AJJ
        #EEEJJ#''')

    thread = FillThread([front_target_text, back_target_text])

    thread.run()

    assert thread.progress is not None
    assert thread.progress.is_success
    assert thread.progress.target_texts == (expected_front_text,
                                            expected_back_text)


def test_multiple_sources_and_target_init():
    target_text = dedent('''\
        ........
        ........
        ........
        ........
        ........
        ........''')
    source_text1 = dedent("""\
        #DCC#
        DDCC#
        DAAAA
        IIIGG
        #IGG#
        """)
    source_text2 = dedent("""\
        #FEE#
        FFEE#
        FBBBB
        JJJHH
        #JHH#
        """)
    source_text3 = dedent("""\
        #CCD#
        #CCDD
        AAAAD
        GGIII
        #GGI#
        """)
    source_text4 = dedent("""\
        #EEF#
        #EEFF
        BBBBF
        HHJJJ
        #HHJ#
        """)
    expected_shape_targets = {'I1': 2, 'O': 2, 'S0': 2, 'T0': 2, 'Z1': 2}

    thread = FillThread([target_text], [source_text1, source_text2, source_text3, source_text4])

    assert isinstance(thread.packer, XPacker)
    assert (thread.packer.width, thread.packer.height) == (8, 6)
    assert thread.packer.target_shape_counts == expected_shape_targets


def test_multiple_sources_and_target_partly_filled():
    target_text = dedent('''\
        AA......
        AA......
        ........
        ........
        ........
        ........''')
    source_text1 = dedent("""\
        #DCC#
        DDCC#
        DAAAA
        IIIGG
        #IGG#
        """)
    source_text2 = dedent("""\
        #FEE#
        FFEE#
        FBBBB
        JJJHH
        #JHH#
        """)
    source_text3 = dedent("""\
        #CCD#
        #CCDD
        AAAAD
        GGIII
        #GGI#
        """)
    source_text4 = dedent("""\
        #EEF#
        #EEFF
        BBBBF
        HHJJJ
        #HHJ#
        """)
    expected_shape_targets = {'I1': 2, 'O': 1, 'S0': 2, 'T0': 2, 'Z1': 2}

    thread = FillThread([target_text], [source_text1, source_text2, source_text3, source_text4])

    assert isinstance(thread.packer, XPacker)
    assert (thread.packer.width, thread.packer.height) == (8, 6)
    assert thread.packer.target_shape_counts == expected_shape_targets
