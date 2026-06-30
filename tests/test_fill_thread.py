from textwrap import dedent

from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.double_block_packer import DoubleBlockPacker
from four_letter_blocks.fill_thread import FillThread
from four_letter_blocks.x_packer import XPacker


# def test_single_target_init():
#     target_text = dedent('''\
#         .....
#         .....
#         ..#..
#         .....
#         .....''')
#     expected_shape_targets = BlockPacker.calculate_target_shape_counts(6)
#
#     thread = FillThread([target_text])
#
#     assert isinstance(thread.packer, XPacker)
#     assert thread.packer.target_shape_counts == expected_shape_targets
#
#
# def test_single_target_run():
#     target_text = dedent('''\
#         .....
#         .###.
#         .###.
#         .###.
#         .....''')
#
#     thread = FillThread([target_text])
#     thread.packer.epochs = 1
#     thread.packer.pool_size = 10
#     thread.packer.is_logging = True
#     thread.run()  # Runs in current thread, not a new one like start().
#
#     assert thread.solutions


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