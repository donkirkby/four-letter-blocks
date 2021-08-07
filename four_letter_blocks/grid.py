import typing
from itertools import count

from four_letter_blocks.square import Square


class Grid:
    def __init__(self, text: str):
        lines = text.splitlines()
        self.height = len(lines)
        self.width = self.height and max(len(line) for line in lines)
        self.squares: typing.List[typing.List[typing.Optional[
            Square]]] = [[None]*(self.width+2) for _ in range(self.height+2)]
        for y, line in enumerate(lines, 1):
            for x, letter in enumerate(line, 1):
                if letter != '#':
                    square = Square(letter)
                    square.x = x-1
                    square.y = y-1
                    self.squares[y][x] = square
        next_number = 1
        for y1 in range(1, self.height+1):
            for x1 in range(1, self.width+1):
                square = self.squares[y1][x1]
                if square is None:
                    continue
                above = self.squares[y1-1][x1]
                if above is None:
                    word = square.letter
                    for y2 in count(y1+1):
                        below = self.squares[y2][x1]
                        if below is None:
                            break
                        word += below.letter
                    if 1 < len(word):
                        square.down_word = word.strip()
                left = self.squares[y1][x1-1]
                if left is None:
                    word = square.letter
                    for x2 in count(x1+1):
                        right = self.squares[y1][x2]
                        if right is None:
                            break
                        word += right.letter
                    if 1 < len(word):
                        square.across_word = word.strip()
                if square.down_word is not None or square.across_word is not None:
                    square.number = next_number
                    next_number += 1

    def __getitem__(self, item):
        x, y = item
        return self.squares[y+1][x+1]

    @property
    def letter_count(self) -> int:
        return sum(square is not None
                   for row in self.squares
                   for square in row)
