from textwrap import dedent

from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.evo_packer import EvoPacker
from four_letter_blocks.fill_thread import FillThread


def test_single_target_init():
    target_text = dedent('''\
        .....
        .....
        ..#..
        .....
        .....''')
    expected_shape_targets = BlockPacker.calculate_target_shape_counts(6)

    thread = FillThread([target_text])

    assert isinstance(thread.packer, EvoPacker)
    assert thread.packer.target_shape_counts == expected_shape_targets


def test_single_target_run():
    target_text = dedent('''\
        .....
        .###.
        .###.
        .###.
        .....''')

    thread = FillThread([target_text])
    thread.packer.epochs = 1
    thread.packer.pool_size = 10
    thread.packer.is_logging = True
    thread.run()  # Runs in current thread, not a new one like start().

    assert thread.solutions


def test_source_and_target_init():
    target_text = dedent('''\
        #...#
        .....
        ..#..
        .....
        #...#''')
    source_text = dedent('''\
        AAABB
        #DABB
        #D#C#
        DDEC#
        EEECC''')
    expected_shape_targets = {'L3': 1, 'O': 1, 'L0': 1, 'J0': 1, 'J3': 1}

    thread = FillThread([target_text], [source_text])

    assert isinstance(thread.packer, EvoPacker)
    assert thread.packer.target_shape_counts == expected_shape_targets
