from textwrap import dedent

import numpy as np
import pytest

from four_letter_blocks.double_block_packer import DoubleBlockPacker


def test_different_space_count():
    front_text = dedent("""\
        #.....#
        ...#...
        .......
        .#.#.#.
        .......
        ...#...
        #.....#""")
    back_text = dedent("""\
        #.....#
        ...#...
        #.....#
        #..#..#
        #.....#
        ...#...
        #.....#""")
    with pytest.raises(ValueError,
                       match=r'No combination of unused counts could be evenly '
                             r'split: \(40 in Front \(7x7\), '
                             r'36 in Back \(7x7\)\)\.'):
        DoubleBlockPacker(front_text,
                          back_text,
                          titles=['Front (7x7)', 'Back (7x7)'])


def test_fill():
    expected_display = dedent("""\
        ABB#CCCCD
        ABB#EEFFD
        AAG#EFFDD
        GGGHEIIII
        ###H#J###
        KKHHJJLLL
        KMMMJ#LNN
        KOMPP#QQN
        OOOPP#QQN
        
        BBA#GCCCC
        BBA#GGGPP
        DAA#MMMPP
        DIIIIM###
        DDEE#FFKK
        ###ENNFFK
        LLLEN#HJK
        QQLON#HJJ
        QQOOO#HHJ""")
    front_text = dedent("""\
        ...#.....
        ...#.....
        ...#.....
        .........
        ###.#.###
        .........
        .....#...
        .....#...
        .....#...""")
    back_text = dedent("""\
        ...#.....
        ...#.....
        ...#.....
        ......###
        ....#....
        ###......
        .....#...
        .....#...
        .....#...""")
    packer = DoubleBlockPacker(front_text, back_text)
    is_filled = packer.fill()

    assert is_filled
    packer.sort_blocks()

    assert packer.display() == expected_display


def test_tiny_fill():
    expected_display = dedent("""\
        #AAB#
        AACBB
        DCCCB
        DDEEE
        #D#E#

        #B#C#
        BBCCC
        BEEED
        AAEDD
        #AAD#""")
    front_text = dedent("""\
        #...#
        .....
        .....
        .....
        #.#.#""")
    back_text = dedent("""\
        #.#.#
        .....
        .....
        .....
        #...#""")
    packer = DoubleBlockPacker(front_text, back_text)
    is_filled = packer.fill()

    assert is_filled
    packer.sort_blocks()

    assert packer.display() == expected_display


def test_already_filled():
    front_text = dedent("""\
        #ABB#
        AAABB
        DDDDC
        EEECC
        #E#C#""")
    back_text = dedent("""\
        #A#C#
        AAACC
        EEEEC
        DDDBB
        #DBB#""")
    expected_display = dedent("""\
        #ABB#
        AAABB
        DDDDC
        EEECC
        #E#C#

        #A#C#
        AAACC
        DDDDC
        EEEBB
        #EBB#""")
    packer = DoubleBlockPacker(front_text, back_text)
    is_filled = packer.fill()

    assert is_filled
    assert packer.display() == expected_display


def xtest_interactive():
    front_text = dedent("""\
         #.....#
         ...#...
         .......
         .#.#.#.
         .......
         ...#...
         #.....#""")
    back_text = dedent("""\
         ....#.#
         .......
         ....#.#
         ...#...
         #.#....
         .......
         #.#....""")
    packer = DoubleBlockPacker(front_text, back_text)
    is_filled = packer.fill()

    assert is_filled
    print()
    print(packer.display())


def test_state():
    front_text = dedent("""\
        AAAC
        ABCC
        BBDC
        BDDD
        """)
    back_text = dedent("""\
        CAAA
        CCBA
        CDBB
        DDDB""")
    expected_state = np.array([[2, 2, 2, 4],
                               [2, 3, 4, 4],
                               [3, 3, 5, 4],
                               [3, 5, 5, 5],
                               [4, 2, 2, 2],
                               [4, 4, 3, 2],
                               [4, 5, 3, 3],
                               [5, 5, 5, 3]])

    packer = DoubleBlockPacker(front_text, back_text)

    double_state = packer.state

    np.testing.assert_array_equal(double_state, expected_state)


# noinspection DuplicatedCode
def test_display():
    packer = DoubleBlockPacker(
        dedent("""\
            #.A#B
            ..ABB
            .AAB.
            .....
            #.#.#"""),
        dedent("""\
            #.#.#
            .....
            B.A..
            BBA..
            #BAA#"""))
    expected_display = dedent("""\
        #.A#B
        ..ABB
        .AAB.
        .....
        #.#.#

        #.#.#
        .....
        B.A..
        BBA..
        #BAA#""")

    assert packer.display() == expected_display


def test_sort_blocks():
    front_text = dedent("""\
        #.....#
        ...#...
        .......
        .#.#.#.
        .......
        ...#...
        #.....#""")
    back_text = dedent("""\
        #.....#
        .......
        #.....#
        ...#...
        #.....#
        .......
        #.....#""")

    expected_display = dedent("""\
        #AAABB#
        CCA#DBB
        ECCDDFF
        E#G#D#F
        EEGGHHF
        IIG#JHH
        #IIJJJ#

        #BBCCJ#
        BBCCJJJ
        #GFFED#
        GGF#EDD
        #GFEED#
        AAAHHII
        #AHHII#""")

    packer = DoubleBlockPacker(front_text, back_text)

    is_filled = packer.fill()
    assert is_filled
    packer.sort_blocks()

    assert packer.display() == expected_display


def test_validate_good():
    front_text = dedent("""\
        #ABB#
        AAABB
        .....
        .....
        #.#.#""")
    back_text = dedent("""\
        #A#.#
        AAA..
        .....
        ...BB
        #.BB#""")

    # No exception.
    DoubleBlockPacker(front_text, back_text)


def test_validate_shapes():
    front_text = dedent("""\
        #ABB#
        AAABB
        .....
        .....
        #.#.#""")
    back_text = dedent("""\
        #A#.#
        AAA..
        B....
        BB...
        #B..#""")

    expected_error = (r'No combination of unused counts and shape counts could '
                      r'be evenly split: \(12 in Front \(7x7\), '
                      r'12 in Back \(7x7\)\); '
                      r'T2: 1, Z0: 1 in Front \(7x7\); '
                      r'S1: 1, T2: 1 in Back \(7x7\)\.')
    with pytest.raises(ValueError, match=expected_error):
        DoubleBlockPacker(front_text,
                          back_text,
                          titles=['Front (7x7)', 'Back (7x7)'])


def test_validate_block_sizes():
    front_text = dedent("""\
        #ABB#
        AAAB.
        .....
        .....
        ###.#""")
    back_text = dedent("""\
        #B#.#
        BBB..
        AA...
        AA...
        #A...""")

    expected_error = r'Bad block size for A in back, B in front\.'
    with pytest.raises(ValueError, match=expected_error):
        DoubleBlockPacker(front_text, back_text)


def test_validate_gap_sizes():
    front_text = dedent("""\
        #B..#
        BB...
        AB...
        AA...
        #A#.#""")
    back_text = dedent("""\
        #.#.#
        ..B..
        ..BBA
        ..BAA
        #..A#""")

    expected_error = r'Bad unused sizes of 3 in 5x5 B, 9 in 5x5 B\.'
    with pytest.raises(ValueError, match=expected_error):
        DoubleBlockPacker(front_text, back_text)


def test_validate_unsolvable():
    front_text = dedent("""\
        #...#
        ...AA
        .BAA.
        .BB..
        #B#.#""")
    back_text = dedent("""\
        #.##.
        ..B..
        .BB..
        AAB..
        #AA.#""")

    expected_error = r'Fill failed in 5x5 A\.'
    with pytest.raises(ValueError, match=expected_error):
        DoubleBlockPacker(front_text, back_text)


def test_validate_warnings():
    front_text = dedent("""\
        #AAA#
        ..A..
        .....
        .....
        #.#.#""")
    back_text = dedent("""\
        #.#.#
        .....
        .....
        ..AAA
        #..A#""")

    expected_error = (r'Found complete word on one block from \(2, 1\) to '
                      r'\(4, 1\) in 5x5 A\.')
    with pytest.raises(ValueError, match=expected_error):
        DoubleBlockPacker(front_text, back_text)


def test_validate_warnings_with_puzzle_titles():
    front_text = dedent("""\
        #AAA#
        ..A..
        .....
        .....
        #.#.#""")
    back_text = dedent("""\
        #.#.#
        .....
        .....
        ..AAA
        #..A#""")

    expected_error = (r'Found complete word on one block from \(2, 1\) to '
                      r'\(4, 1\) in Example 1 \(5x5\)\.')
    with pytest.raises(ValueError, match=expected_error):
        DoubleBlockPacker(front_text, back_text, titles=['Example 1 (5x5)', 'Example 2 (5x5)'])


def test_small_group_init():
    # 24 spaces
    start_text5x5 = dedent("""\
        .....
        .....
        ..#..
        .....
        .....""")

    # 48 spaces
    start_text7x7 = dedent("""\
        .......
        .......
        .......
        ...#...
        .......
        .......
        .......""")

    # 68 spaces
    start_text9x9 = dedent("""\
        #...#...#
        ........#
        ........#
        .........
        #...#...#
        .........
        #........
        #........
        #...#...#""")

    # 44 spaces
    start_text7x7b = dedent("""\
        #.....#
        .......
        .......
        ...#...
        .......
        .......
        #.....#""")
    expected_display = dedent("""\
        .....####
        .....####
        ..#..####
        .....####
        .....####
        #########
        #...#...#
        ........#
        ........#
        .........
        #...#...#
        .........
        #........
        #........
        #...#...#
        
        .......##
        .......##
        .......##
        ...#...##
        .......##
        .......##
        .......##
        #########
        #.....###
        .......##
        .......##
        ...#...##
        .......##
        .......##
        #.....###""")

    packer = DoubleBlockPacker(start_text5x5,
                               start_text7x7,
                               start_text9x9,
                               start_text7x7b)

    assert packer.display() == expected_display

    can_run_slow = False
    if can_run_slow:
        is_filled = packer.fill()
        assert is_filled
        expected_5x5 = dedent("""\
            DECCC
            DEEGC
            DE#GI
            DJGGI
            JJJII""")
        expected_9x9 = dedent("""\
            #AAU#OFF#
            BAAUOOOF#
            BBBUUHHF#
            VVWWWHRRR
            #VVW#HRQ#
            KKKKSSLQQ
            #PPSSTLQM
            #PNNTTLMM
            #PNN#TLM#""")
        expected_7x7 = dedent("""\
            AACCCBD
            AACBBBD
            FFEHHGD
            FEE#HGD
            FJEMHGG
            JJJMMNN
            KKKKMNN""")
        expected_7x7b = dedent("""\
            #IRRRT#
            LISSRTT
            LIISSTU
            LPP#VVU
            LQPVVUU
            QQPOWWW
            #QOOOW#""")
        expected_target_displays = [expected_5x5,
                                    expected_7x7,
                                    expected_9x9,
                                    expected_7x7b]
        assert expected_target_displays == packer.display_targets()


def test_small_group_fill():
    # 24 spaces
    start_text5x5 = dedent("""\
        DECCC
        DEEGC
        DE#GI
        DJGGI
        JJJII""")

    # 48 spaces
    start_text7x7 = dedent("""\
        AACCCBD
        AACBBBD
        FFEHHGD
        FEE#HGD
        FJEMHGG
        JJJMMNN
        KKKKMNN""")

    # 72 spaces
    start_text9x9 = dedent("""\
        #AAU#OFF#
        BAAUOOOF#
        BBBUUHHF#
        .....HRRR
        #...#HRQ#
        KKKKSSLQQ
        #PPSSTLQM
        #PNNTTLMM
        #PNN#TLM#""")

    # 48 spaces
    start_text7x7b = dedent("""\
        #IRRRT#
        LISSRTT
        LIISSTU
        LPP#..U
        LQP..UU
        QQPO...
        #QOOO.#""")

    packer = DoubleBlockPacker(start_text5x5,
                               start_text7x7,
                               start_text9x9,
                               start_text7x7b)

    is_filled = packer.fill()
    assert is_filled
    expected_5x5 = dedent("""\
        BCAAA
        BCCDA
        BC#DE
        BFDDE
        FFFEE""")
    expected_9x9 = dedent("""\
        #GGU#OII#
        HGGUOOOI#
        HHHUUJJI#
        VVWWWJRRR
        #VVW#JRQ#
        KKKKSSLQQ
        #PPSSTLQM
        #PNNTTLMM
        #PNN#TLM#""")
    expected_7x7 = dedent("""\
        NNAAAHL
        NNAHHHL
        IIQPPEL
        IQQ#PEL
        IOQMPEE
        OOOMMGG
        KKKKMGG""")
    expected_7x7b = dedent("""\
        #DRRRT#
        BDSSRTT
        BDDSSTU
        BJJ#VVU
        BCJVVUU
        CCJFWWW
        #CFFFW#""")
    expected_target_displays = (expected_5x5,
                                expected_7x7,
                                expected_9x9,
                                expected_7x7b)
    assert expected_target_displays == packer.display_targets()


def test_small_group_already_filled():
    # 24 spaces
    start_text5x5 = dedent("""\
        ABCCC
        ABBDC
        AB#DE
        AFDDE
        FFFEE""")

    # 48 spaces
    start_text7x7 = dedent("""\
        AACCCBD
        AACBBBD
        FFEHHGD
        FEE#HGD
        FJELHGG
        JJJLLII
        KKKKLII""")

    # 72 spaces
    start_text9x9 = dedent("""\
        #AAC#IFF#
        BAACIIIF#
        BBBCCHHF#
        VVWWWHRRR
        #VVW#HRG#
        KKKKEELGG
        #NNEEDLGM
        #NJJDDLMM
        #NJJ#DLM#""")

    # 48 spaces
    start_text7x7b = dedent("""\
        #ABBBC#
        DAEEBCC
        DAAEECF
        DGG#HHF
        DIGHHFF
        IIGJKKK
        #IJJJK#""")

    packer = DoubleBlockPacker(start_text5x5,
                               start_text7x7,
                               start_text9x9,
                               start_text7x7b)

    is_filled = packer.fill()
    assert is_filled
    expected_5x5 = dedent("""\
        ABCCC
        ABBDC
        AB#DE
        AFDDE
        FFFEE""")
    expected_9x9 = dedent("""\
        #GGI#OLL#
        HGGIOOOL#
        HHHIINNL#
        VVWWWNUUU
        #VVW#NUM#
        QQQQKKRMM
        #TTKKJRMS
        #TPPJJRSS
        #TPP#JRS#""")
    expected_7x7 = dedent("""\
        PPCCCHR
        PPCHHHR
        LLMTTER
        LMM#TER
        LOMSTEE
        OOOSSGG
        QQQQSGG""")
    expected_7x7b = dedent("""\
        #DUUUJ#
        ADKKUJJ
        ADDKKJI
        ANN#VVI
        ABNVVII
        BBNFWWW
        #BFFFW#""")
    expected_target_displays = (expected_5x5,
                                expected_7x7,
                                expected_9x9,
                                expected_7x7b)
    assert expected_target_displays == packer.display_targets()


def xtest_group_fill():
    # TODO: command line tool that suggests placement when blocks don't match,
    # or prints stats and tries to solve when they do match.
    # TODO: cache filtered options for any grid.
    start_text9x9 = dedent("""\
        .....#...
        .....#...
        .........
        .###....#
        ....#....
        #....###.
        .........
        ...#.....
        ...#.....""")

    start_text11x11 = dedent("""\
        ....#......
        ...#...#...
        ....#......
        ...........
        .##...#...#
        .....#.....
        #...#...##.
        ...........
        ......#....
        ...#...#...
        ......#....""")

    start_text13x13 = dedent("""\
        ....#...#....
        ....#...#....
        ....#...#....
        ....#......##
        .........#...
        ###....#.....
        ......#......
        .....#....###
        ...#.........
        ##......#....
        ....#...#....
        ....#...#....
        ....#...#....""")

    start_text11x11b = dedent("""\
        ......#....
        ...#.......
        ......#....
        .......#...
        .##...#...#
        .....#.....
        #...#...##.
        ...#.......
        ....#......
        .......#...
        ....#......""")

    packer = DoubleBlockPacker(start_text9x9,
                               start_text11x11,
                               start_text13x13,
                               start_text11x11b)

    # assert packer.display() == expected_display
    is_filled = packer.fill()
    assert is_filled
