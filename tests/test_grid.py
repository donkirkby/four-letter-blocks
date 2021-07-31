from four_letter_blocks.grid import Grid


def test():
    text = """\
WORD
I##E
L##A
DOLL
"""

    grid = Grid(text)

    letter_i = grid[0, 1]

    assert letter_i.letter == 'I'
