from collections import Counter
from textwrap import dedent

from four_letter_blocks.evo_packer import EvoPacker, Packing


def test_no_rotations():
    shape_counts = Counter({'S0': 1, 'S1': 1, 'L0': 1, 'L1': 1, 'I0': 1})
    start_text = dedent("""\
        .##..
        .....
        ..#..
        .....
        ..##.""")
    # expected_display = dedent("""\
    #     A##BB
    #     AABBC
    #     DA#EC
    #     DEEEC
    #     DD##C""")
    packer = EvoPacker(start_text=start_text)
    packer.is_logging = False

    packer.fill(shape_counts)

    assert '.' not in packer.display()


def test_mutate():
    unused_counts = []
    for _ in range(100):
        shape_counts = Counter({'O': 3})
        start_text = dedent("""\
            .##..
            ...AA
            BB#AA
            BB...
            ..##.""")
        packer = EvoPacker(start_text=start_text)
        start_state = packer.state
        packing = Packing(dict(state=start_state, shape_counts=shape_counts))
        mutate_params = None

        packing.mutate(mutate_params)

        packer2 = EvoPacker(start_state=packing.value['state'])
        used_count = sum(1 for _ in packer2.create_blocks())
        unused_count = sum(packing.value['shape_counts'].values())

        assert used_count + unused_count == 5

        unused_counts.append(unused_count)
    assert min(unused_counts) == 1
    assert max(unused_counts) == 3
