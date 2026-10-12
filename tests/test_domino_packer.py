from textwrap import dedent

from four_letter_blocks.domino_packer import DominoPacker


def test_add_domino():
    grid_text = dedent("""\
        #SORT
        VENUE
        ELENA
        EMITS
        PALS#""")
    expected_display = dedent("""\
        # S O|R T
          -
        V E N U E
        
        E L E N A
        
        E M I T S
        
        P A L S #""")

    packer = DominoPacker(grid_text)

    x1, y1 = (1, 0)
    x2, y2 = (1, 1)
    packer.add_domino((x1, y1), (x2, y2))
    packer.add_domino((3, 0), (2, 0))  # order doesn't matter

    assert packer.display() == expected_display


def test_fill():
    grid_text = dedent("""\
        #SORT
        VENUE
        ELENA
        EMITS
        PALS#""")
    expected_display = dedent("""\
        # S O|R T
          -     -
        V E N U E
            -
        E|L E N|A
        
        E M|I T S
        -     -
        P A|L S #""")

    horizontal_dominoes = ('OR', 'EL', 'NA', 'MI', 'AL', 'RE')
    vertical_dominoes = ('SE', 'TE', 'NE', 'EP', 'LE', 'TS')
    packer = DominoPacker(grid_text, horizontal_dominoes, vertical_dominoes)

    is_filled = packer.fill()

    assert is_filled
    assert packer.display() == expected_display
    assert packer.used_options == set('hOR0 hEL1 hNA2 hMI3 hAL4 '
                                      'vSE0 vTE1 vNE2 vEP3 vTS5 '
                                      'oV oU oS'.split())


def test_fill_fails():
    grid_text = dedent("""\
        #SORT
        VENUE
        ELENA
        EMITS
        PALS#""")

    horizontal_dominoes = ('OR', 'EL', 'NA', 'MI', 'AL', 'RE')
    vertical_dominoes = ('SE', 'TE', 'NE', 'EP', 'LE', 'TX')
    packer = DominoPacker(grid_text, horizontal_dominoes, vertical_dominoes)

    is_filled = packer.fill()

    assert not is_filled
