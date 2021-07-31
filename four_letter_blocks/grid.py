import typing

from four_letter_blocks.square import Square


class Grid:
    def __init__(self, text: str):
        lines = text.splitlines()
        height = len(lines)
        width = max(len(line) for line in lines)
        self.squares: typing.List[typing.List[typing.Optional[
            Square]]] = [[None]*(width+2) for _ in range(height+2)]
        for y, line in enumerate(lines, 1):
            for x, letter in enumerate(line, 1):
                if letter != '#':
                    square = Square(letter)
                    row = self.squares[y]
                    row[x] = square

    def __getitem__(self, item):
        x, y = item
        return self.squares[y+1][x+1]
