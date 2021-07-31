import typing
from collections import defaultdict
from copy import copy
from random import shuffle

from four_letter_blocks.grid import Grid
from four_letter_blocks.square import Square


class Piece:
    def __init__(self, squares: typing.List[Square]):
        self.squares = squares

    def __repr__(self):
        return f"Piece({self.squares!r})"

    @staticmethod
    def parse(text: str, grid: Grid) -> typing.List['Piece']:
        square_lists = defaultdict(list)
        lines = text.splitlines()
        for y, line in enumerate(lines):
            for x, letter in enumerate(line):
                if letter == '#':
                    continue
                square = copy(grid[x, y])
                square.x = x
                square.y = y
                square_list = square_lists[letter]
                square_list.append(square)
        pieces = [Piece(square_list) for square_list in square_lists.values()]
        shuffle(pieces)
        return pieces
