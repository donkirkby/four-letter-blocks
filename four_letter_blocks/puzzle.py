import typing
from dataclasses import dataclass
from itertools import chain
from random import shuffle

from PySide6.QtGui import QPainter

from four_letter_blocks.grid import Grid
from four_letter_blocks.block import Block
from four_letter_blocks.square import Square


@dataclass
class Puzzle:
    grid: Grid
    all_clues: typing.Dict[str, str]
    across_clues: typing.List[str]
    down_clues: typing.List[str]
    blocks: typing.List[Block]

    @staticmethod
    def parse(source_file: typing.IO) -> 'Puzzle':
        sections = parse_sections(source_file)
        grid = Grid(sections[0])
        all_clues = parse_clues(sections[1])
        blocks = Block.parse(sections[2], grid)
        shuffle(blocks)
        next_number = 1
        across_clues = []
        down_clues = []
        for block in blocks:
            for square in block.squares:
                if square.number is not None:
                    square.number = next_number
                    next_number += 1
                    if square.across_word is not None:
                        clue = all_clues[square.across_word]
                        clue = f"{square.number}. {clue}"
                        across_clues.append(clue)
                    if square.down_word is not None:
                        clue = all_clues[square.down_word]
                        clue = f"{square.number}. {clue}"
                        down_clues.append(clue)
        return Puzzle(grid, all_clues, across_clues, down_clues, blocks)

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
                             for block in self.blocks
                             for square in block.squares),
                            (square
                             for row in self.grid.squares
                             for square in row))
        for square in all_squares:
            if square is not None:
                square.size = value
                square.x *= ratio
                square.y *= ratio

    def draw_blocks(self, painter: QPainter, square_size: int = None):
        window_width = painter.window().width()
        if square_size is None:
            square_size = window_width // 16
        self.square_size = square_size
        gap = square_size / 2
        x = y = self.square_size
        line_height = 0
        x_limit = painter.window().width() - self.square_size
        for block in self.blocks:
            if x_limit < x + block.width:
                x = self.square_size
                y += line_height + gap
                line_height = 0
            block.x = x
            block.y = y
            block.draw(painter)
            line_height = max(line_height, block.height)
            x += block.width + gap

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

    def format_grid(self) -> str:
        rows = []
        for y in range(self.grid.height):
            row = []
            for x in range(self.grid.width):
                cell = self.grid[x, y]
                if cell is None:
                    letter = '#'
                else:
                    letter = cell.letter
                row.append(letter)
            rows.append(row)
        grid_text = '\n'.join(''.join(row) for row in rows)

        return grid_text

    def format_clues(self) -> str:
        return '\n'.join(f'{word} - {clue}'
                         for word, clue in sorted(self.all_clues.items()))

    def format_blocks(self) -> str:
        rows = []
        for y in range(self.grid.height):
            rows.append(['#'] * self.grid.width)
        ascii_start = ord('A')
        for i, block in enumerate(self.blocks, ascii_start):
            block_letter = chr(i)
            for square in block.squares:
                x = square.x
                y = square.y
                rows[y][x] = block_letter
        return '\n'.join(''.join(row) for row in rows)


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
    if 3 < section_count:
        raise ValueError(f'Expected 3 sections, found {section_count}.')
    sections.extend([''] * (3 - section_count))
    return sections


def parse_clues(text):
    clues: typing.Dict[str, str] = {}
    pairs = text.splitlines(keepends=False)
    for pair in pairs:
        word, clue = pair.split('-', maxsplit=1)
        word = word.strip()
        clues[word] = clue.strip()
    return clues
