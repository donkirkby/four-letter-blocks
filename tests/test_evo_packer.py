from collections import Counter
from textwrap import dedent

import numpy as np

from four_letter_blocks.evo_packer import EvoPacker, Packing,\
    PackingFitnessCalculator, FitnessScore, distance_ranking, ranked_offsets


def test_no_rotations():
    shape_counts = Counter({'S0': 1, 'S1': 1, 'L0': 1, 'L1': 1, 'I0': 1})
    start_text = dedent("""\
        .##..
        .....
        ..#..
        .....
        ..##.""")
    # Block letters don't necessarily match.
    expected_display = dedent("""\
        A##BB
        AABBC
        DA#EC
        DEEEC
        DD##C""")
    packer = EvoPacker(start_text=start_text)
    packer.is_logging = False

    is_filled = packer.fill(shape_counts)
    packer.sort_blocks()

    assert is_filled
    assert packer.display() == expected_display


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
        packing = Packing(dict(state=start_state,
                               shape_counts=shape_counts,
                               can_rotate=True))
        mutate_params = None

        packing.mutate(mutate_params)

        packer2 = EvoPacker(start_state=packing.value['state'])
        used_count = sum(1 for _ in packer2.create_blocks())
        unused_count = sum(packing.value['shape_counts'].values())

        assert used_count + unused_count == 5

        unused_counts.append(unused_count)
    assert min(unused_counts) == 1
    assert max(unused_counts) == 3


def test_fitness():
    start_state = EvoPacker(start_text=dedent("""\
        .##..
        ...AA
        ..#AA
        BBCCC
        BB##C""")).state
    packing = Packing(dict(state=start_state, shape_counts={'O': 3}))
    calculator = PackingFitnessCalculator()

    fitness = calculator.calculate(packing)

    assert fitness == FitnessScore(empty_spaces=-8, empty_area=-0.6)


def test_fitness_full():
    start_state = EvoPacker(start_text=dedent("""\
        D##EA
        DEEEA
        DD#AA
        BBCCC
        BB##C""")).state
    packing = Packing(dict(state=start_state, shape_counts={}))
    calculator = PackingFitnessCalculator()

    fitness = calculator.calculate(packing)

    assert fitness == FitnessScore(empty_spaces=0,
                                   empty_area=0,
                                   warning_count=-3)


def test_distance_ranking():
    expected_ranking = np.fromstring("""\
        22  13  12  11  21
        14   4   3   2  10
        15   5   0   1   9
        16   6   7   8  20
        23  17  18  19  24
    """, dtype=int, sep=" ").reshape(5, 5)

    ranking = distance_ranking(5)

    assert np.array_equal(ranking, expected_ranking)


def test_ranked_offsets():
    expected_positions = np.array(
        [[0, 0], [0, 1], [-1, 1], [-1, 0], [-1, -1], [0, -1], [1, -1], [1, 0],
         [1, 1], [0, 2], [-1, 2], [-2, 1], [-2, 0], [-2, -1], [-1, -2], [0, -2],
         [1, -2], [2, -1], [2, 0], [2, 1], [1, 2], [-2, 2], [-2, -2], [2, -2],
         [2, 2]])

    positions = ranked_offsets(3)

    assert np.array_equal(positions, expected_positions)


def test_distance_ranking_big():
    ranking = distance_ranking(15)

    assert np.max(ranking) == 15*15 - 1
