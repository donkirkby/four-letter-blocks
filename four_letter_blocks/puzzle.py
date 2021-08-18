import re
import typing
from dataclasses import dataclass, field
from html import escape
from itertools import chain
from random import shuffle

from PySide6.QtGui import QPainter, Qt, QTextDocument

from four_letter_blocks.grid import Grid
from four_letter_blocks.block import Block
from four_letter_blocks.square import Square


@dataclass
class Puzzle:
    HINT = 'Clue numbers are shuffled: 1 Across might not be in the top left.'

    title: str
    grid: Grid
    all_clues: typing.Dict[str, str]
    blocks: typing.List[Block]
    across_clues: typing.List[str] = field(init=False)
    down_clues: typing.List[str] = field(init=False)

    @staticmethod
    def parse(source_file: typing.IO) -> 'Puzzle':
        sections = split_sections(source_file)
        return Puzzle.parse_sections(*sections)

    @staticmethod
    def parse_sections(title: str,
                       grid_text: str,
                       clues_text: str,
                       blocks_text: str,
                       old_clues: typing.Dict[str, str] = None) -> 'Puzzle':
        if old_clues is None:
            old_clues = {}
        grid = Grid(grid_text)
        parsed_clues = parse_clues(clues_text)
        for word, clue in parsed_clues.items():
            old_clues[word] = clue
        all_clues = {}
        blocks = Block.parse(blocks_text, grid)
        for block in blocks:
            for square in block.squares:
                if square.number is None:
                    continue
                for word in (square.across_word, square.down_word):
                    if word is None:
                        continue
                    old_clue = old_clues.get(word, '')
                    clue = parsed_clues.get(word, old_clue)
                    all_clues[word] = clue
        return Puzzle(title, grid, all_clues, blocks)

    def __post_init__(self):
        self.across_clues = []
        self.down_clues = []
        self.number_clues()

    def number_clues(self):
        self.across_clues.clear()
        self.down_clues.clear()
        references = {}  # {word: reference} e.g., {'FOO': '1 Across'}
        next_number = 1
        for block in self.blocks:
            for square in block.squares:
                if square.number is None:
                    continue
                square.number = next_number
                next_number += 1
                for word, clues, direction in (
                        (square.across_word, self.across_clues, 'Across'),
                        (square.down_word, self.down_clues, 'Down')):

                    if word is None:
                        continue
                    clue = self.all_clues[word]
                    references[word] = f'{square.number} {direction}'
                    formatted_clue = f"{square.number}. {clue}"
                    clues.append(formatted_clue)
        for clues in (self.across_clues, self.down_clues):
            for i, clue in enumerate(clues):
                matches = list(re.finditer(r'[A-Z]{2,}', clue))
                if not matches:
                    continue
                matches.reverse()
                clue_chars = list(clue)
                for match in matches:
                    word = match.group(0)
                    try:
                        reference = references[word]
                    except KeyError:
                        continue
                    clue_chars[match.start():match.end()] = reference
                clues[i] = ''.join(clue_chars)

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

    def draw_blocks(self, painter: QPainter, square_size: int = None) -> int:
        """ Draw all blocks on a painter. Return the height of the image. """
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
        y += line_height + self.square_size
        return y

    def draw_clues(self, painter: QPainter, square_size: int = None):
        window_width = painter.window().width()
        window_height = painter.window().height()
        if square_size is None:
            square_size = window_width // 16
        self.square_size = square_size
        letter_size = round(square_size * 0.5)

        font = painter.font()
        font.setPixelSize(round(square_size * Square.LETTER_SIZE))
        painter.setFont(font)
        painter.drawText(0, 0,
                         window_width, square_size,
                         Qt.AlignHCenter,
                         self.title)

        font.setPixelSize(round(letter_size * Square.LETTER_SIZE))
        painter.setFont(font)
        painter.drawText(letter_size, letter_size * 3, self.HINT)
        painter.drawText(letter_size, letter_size*4, 'Across')
        for i, clue in enumerate(self.across_clues, 5):
            painter.drawText(letter_size, i * letter_size, clue)

        middle = window_width // 2
        painter.drawText(middle, letter_size*4, 'Down')
        for i, clue in enumerate(self.down_clues, 5):
            painter.drawText(middle, i * letter_size, clue)

        painter.drawText(0, window_height-square_size,
                         window_width, square_size,
                         Qt.AlignHCenter,
                         'https://donkirkby.github.io/four-letter-blocks')

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
            block_letter = '?' if block.marker == Block.UNUSED else chr(i)
            for square in block.squares:
                x = square.x
                y = square.y
                rows[y][x] = block_letter
        return '\n'.join(''.join(row) for row in rows)

    def display_block_sizes(self) -> str:
        correct_markers = {block.marker
                           for block in self.blocks
                           if len(block.squares) == 4
                           and len(block.marker) == 1}
        correct_count = len(correct_markers)
        incorrect_counts = {block.marker: len(block.squares)
                            for block in self.blocks
                            if block.marker not in correct_markers}
        incorrect_items = sorted(incorrect_counts.items())
        incorrect_display = ', '.join(f'{marker}={n}'
                                      for marker, n in incorrect_items)
        display_terms = []
        if correct_count:
            display_terms.append(f'{correct_count}x4')
        if incorrect_display:
            display_terms.append(incorrect_display)
        return ', '.join(display_terms)

    def shuffle(self):
        shuffle(self.blocks)
        self.number_clues()

    def build_clues(self, document: QTextDocument):
        font_size = document.defaultFont().pixelSize()
        padding = font_size // 5
        document.setDefaultStyleSheet(f"""\
h1 {{text-align: center}}
hr.footer {{line-height:10px}}
td {{padding: {padding} }}
td.num {{text-align: right}}
a {{color: black}}
""")
        across_table = build_clue_table(self.across_clues)
        down_table = build_clue_table(self.down_clues)
        document.setHtml(f"""\
<h1>{escape(self.title)}</h1>
<p>{escape(self.HINT)}</p>
<hr>
<table>
<tr><td>Across</td><td>Down</td></tr>
<tr><td>
{across_table}
</td><td>
{down_table}
</td></tr>
</table>
<hr class="footer">
<center><a href="https://donkirkby.github.io/four-letter-blocks"
>https://donkirkby.github.io/four-letter-blocks</a></center>
""")


def build_clue_table(clues: typing.Sequence[str]) -> str:
    rows = []
    for clue in clues:
        number, text = clue.split('.', 1)
        rows.append(f'<tr><td class="num">{number}.</td>'
                    f'<td>{escape(text)}</td></tr>')
    return f'<table>{"".join(rows)}</table>'


def split_sections(source_file):
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
    if 4 < section_count:
        raise ValueError(f'Expected 4 sections, found {section_count}.')
    sections.extend([''] * (4 - section_count))
    return sections


def parse_clues(text):
    clues: typing.Dict[str, str] = {}
    pairs = text.splitlines(keepends=False)
    for pair in pairs:
        try:
            word, clue = pair.split('-', maxsplit=1)
        except ValueError:
            continue
        word = word.strip()
        if word:
            clues[word] = clue.strip()
    return clues
