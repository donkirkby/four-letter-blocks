from textwrap import dedent

import numpy as np
import pytest

from four_letter_blocks.double_block_packer import DoubleBlockPacker


def test_different_space_count():
    front_text = dedent("""\
        #?????#
        ???#???
        ???????
        ?#?#?#?
        ???????
        ???#???
        #?????#""")
    back_text = dedent("""\
        #?????#
        ???#???
        ??????#
        ##?#?##
        #??????
        ???#???
        #?????#""")
    with pytest.raises(ValueError, match=r'Different space counts: 40 and 36\.'):
        DoubleBlockPacker(front_text, back_text, tries=100)


def test_fill():
    expected_display = dedent("""\
        #ABBBB#
        AAA#CCD
        EFFFCCD
        E#F#G#D
        EHHHGID
        EHJ#GII
        #JJJGI#
        
        HHHFFF#
        D#H#FCC
        DBBBBCC
        D#E#A#G
        DIEAAAG
        IIE#J#G
        #IEJJJG""")
    front_text = dedent("""\
        #.BBBB#
        ...#..D
        ......D
        .#.#.#D
        ......D
        ...#...
        #.....#""")
    back_text = dedent("""\
        ......#
        D#.#...
        DBBBB..
        D#.#.#.
        D......
        ...#.#.
        #......""")
    packer = DoubleBlockPacker(front_text, back_text, tries=40_000)
    packer.fill()

    assert packer.is_full
    packer.sort_blocks()

    assert packer.display() == expected_display


def test_fill_rectangle():
    expected_display = dedent("""\
        #ABBBB#
        AAA#CCD
        EFFFCCD
        E#F#G#D
        EHHHGID
        EHJ#GII
        #KJJGI#
        KKLJMM#
        KLLLMM#
        
        HHHFFF#
        D#H#FCC
        DBBBBCC
        D#E#A#G
        DIEAAAG
        IIE#K#G
        #IEJKKG
        MMJJLK#
        MMJLLL#""")
    front_text = dedent("""\
        #.BBBB#
        ...#..D
        ......D
        .#.#.#D
        ......D
        ...#...
        #.....#
        ......#
        ......#""")
    back_text = dedent("""\
        ......#
        D#.#...
        DBBBB..
        D#.#.#.
        D......
        ...#.#.
        #......
        ......#
        ......#""")
    packer = DoubleBlockPacker(front_text, back_text, tries=40_000)
    packer.fill()

    assert packer.is_full
    packer.sort_blocks()

    assert packer.display() == expected_display


def test_slots_shuffled():
    front_text = dedent("""\
        #?????#
        ???#???
        ???????
        ?#?#?#?
        ???????
        ???#???
        #?????#""")
    back_text = dedent("""\
        ??????#
        ?#?#???
        ???????
        ?#?#?#?
        ???????
        ???#?#?
        #??????""")
    displays = set()

    for _ in range(10):
        packer = DoubleBlockPacker(front_text, back_text, tries=400)
        packer.are_slots_shuffled = True

        packer.fill()

        assert packer.is_full
        packer.sort_blocks()
        displays.add(packer.display())

    assert len(displays) > 1
    for display in displays:
        print('---')
        print(display)


def test_state():
    front_text = dedent("""\
        AAA
        A#B
        BBB""")
    back_text = dedent("""\
        AAB
        A#B
        ABB""")
    expected_state = np.array([[2, 2, 2],
                               [2, 1, 3],
                               [3, 3, 3],
                               [2, 2, 3],
                               [2, 1, 3],
                               [2, 3, 3]])

    packer = DoubleBlockPacker(front_text, back_text, tries=400)

    double_state = packer.state

    np.testing.assert_array_equal(double_state, expected_state)


# noinspection DuplicatedCode
def test_remove_block():
    packer = DoubleBlockPacker(
        front_text=dedent("""\
            #..#.
            ...B.
            AA#B.
            AA.BB
            .#..#"""),
        back_text=dedent("""\
            #AA.#
            .AA..
            ..#B.
            ...B.
            #.BB#"""))
    expected_display = dedent("""\
        #..#.
        .....
        AA#..
        AA...
        .#..#
        
        #AA.#
        .AA..
        ..#..
        .....
        #...#""")

    shape = packer.remove_block(1, 3)

    assert shape == 'L0'
    assert packer.display() == expected_display


# noinspection DuplicatedCode
def test_start_state():
    packer1 = DoubleBlockPacker(
        front_text=dedent("""\
            #..#.
            ...B.
            AA#B.
            AA.BB
            .#..#"""),
        back_text=dedent("""\
            #AA.#
            .AA..
            ..#B.
            ...B.
            #.BB#"""))
    expected_display = dedent("""\
        #..#.
        ...B.
        AA#B.
        AA.BB
        .#..#

        #AA.#
        .AA..
        ..#B.
        ...B.
        #.BB#""")

    start_state = packer1.state.copy()
    packer2 = DoubleBlockPacker(start_state=start_state)

    assert packer2.display() == expected_display


def test_sort_blocks():
    front_text = dedent("""\
        #AAAAB#
        CDD#BBE
        CDDFFBE
        C#G#F#E
        CGGGFHE
        III#HHH
        #IJJJJ#""")
    back_text = dedent("""\
        AAAABB#
        C#D#BEE
        CDDDBEE
        C#F#G#H
        CFFFGGH
        III#G#H
        #IJJJJH""")

    expected_display = dedent("""\
        #AAAAB#
        CDD#BBE
        CDDFFBE
        C#G#F#E
        CGGGFHE
        III#HHH
        #IJJJJ#
        
        AAAAFF#
        C#G#FDD
        CGGGFDD
        C#H#B#E
        CHHHBBE
        III#B#E
        #IJJJJE""")

    packer = DoubleBlockPacker(front_text, back_text)

    packer.sort_blocks()

    assert packer.display() == expected_display
