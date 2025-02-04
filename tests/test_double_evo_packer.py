from collections import Counter
from textwrap import dedent
from unittest.mock import patch

import pytest

from four_letter_blocks.double_block_packer import DoubleBlockPacker
from four_letter_blocks.double_evo_packer import DoubleEvoPacker
from four_letter_blocks.evo_packer import Packing


@pytest.mark.skip(reason="Too slow for a unit test.")
def test_double_evo_packer():
    front_text = dedent("""\
        ???#?????
        ???#?????
        ???#?????
        ??????###
        ????#????
        ###??????
        ?????#???
        ?????#???
        ?????#???""")
    back_text = dedent("""\
        ???#?????
        ???#?????
        ???#?????
        ?????????
        ###?#?###
        ?????????
        ?????#???
        ?????#???
        ?????#???""")
    packer = DoubleEvoPacker(front_text, back_text, tries=5000)
    packer.force_fours = True
    packer.epochs = 50
    packer.pool_size = 100
    packer.is_logging = True
    packer.fill()

    assert packer.is_full
    packer.sort_blocks()
    print('---')
    print(packer.display())
    print(f'{packer.tries} tries left.')
    assert False


@patch('four_letter_blocks.evo_packer.randrange')
@patch('four_letter_blocks.evo_packer.choices')
@pytest.mark.skip(reason="not implemented yet, only mutating")
def test_pair(mock_choices, mock_randrange):
    mock_choices.side_effect = [['mix']]
    mock_randrange.side_effect = [0, 0, 6, 6]

    shape_counts1 = Counter()
    front_text1 = dedent("""\
        #AAAAB#
        CDD#BBE
        CDDFFBE
        C#G#F#E
        CGGGFHE
        III#HHH
        #IJJJJ#""")
    back_text1 = dedent("""\
        AAAAFF#
        C#G#FDD
        CGGGFDD
        C#H#B#E
        CHHHBBE
        III#B#E
        #IJJJJE""")
    front_text2 = dedent("""\
        #ABBBB#
        AAA#CCD
        EFFFCCD
        E#F#G#D
        EHGGGID
        EHH#III
        #HJJJJ#""")
    back_text2 = dedent("""\
        DBBBBA#
        D#H#AAA
        DHHFFFE
        D#H#F#E
        CCJJJJE
        CCI#G#E
        #IIIGGG""")
    expected_display = dedent("""\
        #AAAA.#
        C..#...
        C......
        C#.#.#.
        C......
        ...#...
        #.JJJJ#

        AAAA..#
        C#.#...
        C......
        C#.#.#.
        C.JJJJ.
        ...#.#.
        #......
        """)
    packer1 = DoubleEvoPacker(front_text=front_text1, back_text=back_text1)
    packing1 = Packing(dict(state=packer1.state,
                            shape_counts=shape_counts1,
                            can_rotate=False,
                            packer_class=DoubleBlockPacker))
    shape_counts2 = Counter()
    packer2 = DoubleEvoPacker(front_text=front_text2, back_text=back_text2)
    packing2 = Packing(dict(state=packer2.state,
                            shape_counts=shape_counts2,
                            can_rotate=False,
                            packer_class=DoubleBlockPacker))
    expected_shape_counts = {'I0': 2, 'O': 2}

    child = packing1.pair(packing2, {})

    assert packer2.display(child.value['state']) == expected_display
    assert child.value['shape_counts'] == expected_shape_counts
