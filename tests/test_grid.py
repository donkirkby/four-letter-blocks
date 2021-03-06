from four_letter_blocks.grid import Grid


def test_letter():
    text = """\
WORD
I##E
L##A
DOLL
"""

    grid = Grid(text)

    letter_i = grid[0, 1]

    assert letter_i.letter == 'I'


def test_black_square():
    text = """\
WORD
I##E
L##A
DOLL
"""

    grid = Grid(text)

    square = grid[1, 1]

    assert square is None


def test_words():
    text = """\
WORD
I##R
R##A
EXIT
"""

    grid = Grid(text)

    letter_w = grid[0, 0]
    letter_d = grid[3, 0]
    letter_x = grid[1, 3]

    assert letter_x.across_word is None
    assert letter_x.down_word is None
    assert letter_d.across_word is None
    assert letter_d.down_word == 'DRAT'
    assert letter_w.across_word == 'WORD'
    assert letter_w.down_word == 'WIRE'

    assert letter_x.number is None
    assert letter_w.number == 1
    assert letter_d.number == 2

    assert letter_x.x == 1
    assert letter_x.y == 3


def test_spaces_break_words():
    text = """\
WO #
I##R
R##A
EXIT
"""

    grid = Grid(text)

    letter_w = grid[0, 0]

    assert letter_w.across_word == 'WO'


def test_letter_count():
    text = """\
WORD
I##R
R##A
EXIT
"""

    grid = Grid(text)

    assert grid.letter_count == 12
