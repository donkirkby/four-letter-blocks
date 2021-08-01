import typing
from dataclasses import dataclass
from itertools import chain
from random import shuffle

from PySide6.QtGui import QPainter

from four_letter_blocks.grid import Grid
from four_letter_blocks.piece import Piece
from four_letter_blocks.square import Square


@dataclass
class Puzzle:
    grid: Grid
    across_clues: typing.List[str]
    down_clues: typing.List[str]
    pieces: typing.List[Piece]

    @staticmethod
    def parse(source_file: typing.IO) -> 'Puzzle':
        sections = parse_sections(source_file)
        grid = Grid(sections[0])
        across_dict = parse_clues(sections[1], 'across')
        down_dict = parse_clues(sections[2], 'down')
        pieces = Piece.parse(sections[3], grid)
        shuffle(pieces)
        next_number = 1
        across_clues = []
        down_clues = []
        for piece in pieces:
            for square in piece.squares:
                if square.number is not None:
                    square.number = next_number
                    next_number += 1
                    if square.across_word is not None:
                        clue = across_dict[square.across_word]
                        clue = f"{square.number}. {clue}"
                        across_clues.append(clue)
                    if square.down_word is not None:
                        clue = down_dict[square.down_word]
                        clue = f"{square.number}. {clue}"
                        down_clues.append(clue)
        return Puzzle(grid, across_clues, down_clues, pieces)

    @property
    def square_size(self) -> int:
        for row in self.grid.squares:
            for square in row:
                if square is not None:
                    return square.size

    @square_size.setter
    def square_size(self, value: int):
        ratio = value / self.square_size
        all_squares = chain((square
                             for piece in self.pieces
                             for square in piece.squares),
                            (square
                             for row in self.grid.squares
                             for square in row))
        for square in all_squares:
            if square is not None:
                square.size = value
                square.x *= ratio
                square.y *= ratio

    def draw_pieces(self, painter: QPainter, square_size: int = None):
        window_width = painter.window().width()
        if square_size is None:
            square_size = window_width // 16
        self.square_size = square_size
        gap = square_size / 2
        x = y = self.square_size
        line_height = 0
        x_limit = painter.window().width() - self.square_size
        for piece in self.pieces:
            if x_limit < x + piece.width:
                x = self.square_size
                y += line_height + gap
                line_height = 0
            piece.x = x
            piece.y = y
            piece.draw(painter)
            line_height = max(line_height, piece.height)
            x += piece.width + gap

    def draw_clues(self, painter: QPainter, square_size: int = None):
        window_width = painter.window().width()
        if square_size is None:
            square_size = window_width // 16
        self.square_size = square_size
        letter_size = round(square_size * 0.75)
        font = painter.font()
        font.setPixelSize(round(letter_size * Square.LETTER_SIZE))
        painter.setFont(font)
        painter.drawText(letter_size, letter_size, 'Across')
        for i, clue in enumerate(self.across_clues, 2):
            painter.drawText(letter_size, i * letter_size, clue)

        middle = window_width // 2
        painter.drawText(middle, letter_size, 'Down')
        for i, clue in enumerate(self.down_clues, 2):
            painter.drawText(middle, i * letter_size, clue)


def parse_sections(source_file):
    sections: typing.List[str] = []
    lines: typing.List[str] = []
    for line in chain(source_file, '\n'):
        line = line.rstrip()
        if line:
            lines.append(line)
        else:
            section = '\n'.join(lines)
            if section:
                sections.append(section)
            lines.clear()
    section_count = len(sections)
    if section_count != 4:
        exit(f'Expected 4 sections, found {section_count}.')
    return sections


def parse_clues(text, label):
    clues: typing.Dict[str, str] = {}
    pairs = text.splitlines(keepends=False)
    if pairs[0].lower() == label:
        pairs.pop(0)
    for pair in pairs:
        word, clue = pair.split('-', maxsplit=1)
        word = word.strip()
        clues[word] = clue.strip()
    return clues
