import re
import typing
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from html import escape
from itertools import chain
from operator import attrgetter
from random import shuffle
from textwrap import dedent

from PySide6.QtGui import QPainter, QTextDocument, QTextCursor

from four_letter_blocks.clue import Clue
from four_letter_blocks.grid import Grid
from four_letter_blocks.block import Block


@dataclass
class Puzzle:
    HINT = 'Clue numbers are shuffled: 1 Across might not be the top left.'
    SUIT_HINT = "Each corner has its own suit."
    DEFAULT_ROW_LENGTH = 16  # Number of squares across a diagram.

    title: str
    grid: Grid
    all_clues: typing.Dict[str, Clue]
    blocks: typing.List[Block]
    across_clues: typing.List[Clue] = field(init=False)
    down_clues: typing.List[Clue] = field(init=False)
    use_suits: bool = False
    use_text: bool = True

    @staticmethod
    def parse(source_file: typing.IO) -> 'Puzzle':
        sections = split_sections(source_file)
        return Puzzle.parse_sections(*sections)

    @staticmethod
    def parse_sections(title: str,
                       grid_text: str,
                       clues_text: str,
                       blocks_text: str,
                       old_clues: typing.Dict[str, Clue] = None) -> 'Puzzle':
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
                    old_clue = old_clues.get(word, Clue(''))
                    clue = parsed_clues.get(word, old_clue)
                    all_clues[word] = clue
        return Puzzle(title, grid, all_clues, blocks)

    def __post_init__(self):
        self.across_clues = []
        self.down_clues = []
        self.use_suits = 121 < self.grid.width * self.grid.height
        self.number_clues()

    def number_clues(self):
        self.across_clues.clear()
        self.down_clues.clear()
        references = {}  # {word: reference} e.g., {'FOO': '1 Across'}
        used_numbers = Counter()  # {suit: used_number}
        suits = list('CDHS')
        suit_order = [None] * 4
        x_mid = self.grid.width / 2
        y_mid = self.grid.height / 2
        for block in self.blocks:
            for square in block.squares:
                if square.number is None:
                    continue
                if not self.use_suits:
                    suit_slot = None
                elif square.x <= x_mid and square.y < y_mid:
                    suit_slot = 0
                elif x_mid < square.x and square.y <= y_mid:
                    suit_slot = 1
                elif x_mid <= square.x and y_mid < square.y:
                    suit_slot = 2
                else:
                    suit_slot = 3
                used_number = used_numbers[suit_slot]
                used_number += 1
                square.number = used_number
                used_numbers[suit_slot] = used_number
                if suit_slot is not None:
                    if suit_order[suit_slot] is None:
                        suit_order[suit_slot] = suits.pop(0)
                    square.suit = suit_order[suit_slot]
                    self.grid[square.x, square.y].suit = square.suit

                for word, clues, direction in (
                        (square.across_word, self.across_clues, 'Across'),
                        (square.down_word, self.down_clues, 'Down')):

                    if word is None:
                        continue
                    clue = self.all_clues[word]
                    clue.number = square.number
                    clue.suit = square.suit
                    references[word] = f'{square.display_number()} {direction}'
                    clues.append(clue)
        for clues in (self.across_clues, self.down_clues):
            for i, clue in enumerate(clues):
                matches = list(re.finditer(r'[A-Z]{2,}', clue.text))
                if not matches:
                    continue
                matches.reverse()
                clue_chars = list(clue.text)
                for match in matches:
                    word = match.group(0)
                    try:
                        reference = references[word]
                    except KeyError:
                        continue
                    clue_chars[match.start():match.end()] = reference
                clue.text_with_reference = ''.join(clue_chars)
        clue_key = attrgetter('suit', 'number')
        self.across_clues.sort(key=clue_key)
        self.down_clues.sort(key=clue_key)

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

    @property
    def extras(self):
        messages = []
        pairs = 'JLSZ'
        shape_counts = self.shape_counts
        for shape, count in sorted(shape_counts.items()):
            pair_index = pairs.find(shape)
            if pair_index < 0:
                if count % 2 != 0:
                    messages.append(f'{shape}+')
            else:
                mirror = pairs[pair_index+1 - 2*(pair_index % 2)]
                mirror_count = shape_counts[mirror]
                if count > mirror_count:
                    messages.append(f'{shape}+{count-mirror_count}')
        return ', '.join(messages)

    def draw_blocks(self,
                    painter: QPainter,
                    square_size: int = None,
                    row_index: int = None,
                    x: int = 0,
                    y: int = 0) -> int:
        """ Draw all blocks on a painter. Return the height of the image. """
        window_width = painter.window().width()
        if square_size is None:
            square_size = window_width // self.DEFAULT_ROW_LENGTH
        self.square_size = square_size
        gap = square_size / 2
        x_start = x
        x += self.square_size
        if row_index is None:
            y += square_size
        else:
            y += gap
        line_height = 0
        row_count = 0
        x_limit = painter.window().width() - self.square_size
        is_active_row = False
        for block in self.sorted_blocks():
            if x_limit < x + block.width - x_start:
                x = self.square_size
                if is_active_row:
                    y += line_height + gap
                row_count += 1
                line_height = 0
            is_active_row = row_index is None or row_index == row_count
            if is_active_row:
                block.x = x
                block.y = y
                block.draw(painter, use_text=self.use_text)
            line_height = max(line_height, block.height)
            x += block.width + gap
        if row_index is None:
            y += line_height + square_size
        elif is_active_row:
            y += line_height
        return y

    def sorted_blocks(self):
        """ Blocks sorted by increasing height. """
        return sorted(self.blocks, key=lambda b: b.height)

    def row_heights(self,
                    window_width: int = None,
                    square_size: int = None) -> typing.List[int]:
        """ Height needed to draw each row of blocks. """
        row_heights = []
        if square_size is None and window_width is not None:
            square_size = window_width // self.DEFAULT_ROW_LENGTH
        elif square_size is not None and window_width is None:
            window_width = square_size * self.DEFAULT_ROW_LENGTH
        elif window_width is None:
            square_size = self.square_size
            window_width = square_size * self.DEFAULT_ROW_LENGTH
        self.square_size = square_size
        gap = self.square_size / 2
        x = self.square_size
        line_height = 0
        x_limit = window_width - square_size
        for block in self.sorted_blocks():
            if x_limit < x + block.width:
                x = self.square_size
                row_heights.append(line_height + gap)
                line_height = 0
            line_height = max(line_height, block.height)
            x += block.width + gap
        if 0 < line_height:
            # Count final row
            row_heights.append(line_height + gap)
        return row_heights

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
        return '\n'.join(f'{word} - {clue.text}'
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

    def display_block_summary(self) -> str:
        sections = []
        block_sizes = self.display_block_sizes()
        sections.append(f'Block sizes: {block_sizes}')
        shape_count_text = ', '.join(
            f'{shape}: {count}'
            for shape, count in sorted(self.shape_counts.items()))
        if shape_count_text:
            sections.append('Shapes: ' + shape_count_text)
        return ', '.join(sections)

    def check_style(self) -> typing.List[str]:
        warnings = list(self.check_symmetry())
        warnings.extend(self.check_repeats())
        warnings.extend(self.check_word_length())
        return warnings

    def check_word_length(self):
        short_warnings = []
        complete_warnings = []
        for block in self.blocks:
            for square1 in block.squares:
                for word, dx, dy in ((square1.across_word, 1, 0),
                                     (square1.down_word, 0, 1)):
                    if word is None:
                        continue
                    x1 = square1.x
                    y1 = square1.y
                    word_length = len(word)
                    start = (x1 + 1, y1 + 1)
                    end = (x1 + word_length * dx + dy, y1 + word_length * dy + dx)
                    if word_length == 2:
                        short_warnings.append(
                            (start,
                             end,
                             f'two-letter word at {start} and {end}'))
                    if block.marker == Block.UNUSED:
                        continue
                    block_coordinates = block.calculate_coordinates()
                    for i in range(1, word_length):
                        square2 = self.grid[x1 + i * dx, y1 + i * dy]
                        if (square2.x, square2.y) not in block_coordinates:
                            break
                    else:
                        complete_warnings.append((
                            start,
                            end,
                            f'complete word on one block from {start} to {end}'))
        short_warnings.sort()
        yield from (warning for start, end, warning in short_warnings)
        complete_warnings.sort()
        yield from (warning for start, end, warning in complete_warnings)

    def check_repeats(self):
        word_counts = Counter()
        for x in range(self.grid.width):
            for y in range(self.grid.height):
                square = self.grid[x, y]
                if square is not None:
                    word_counts[square.across_word] += 1
                    word_counts[square.down_word] += 1
        word_counts[None] = 0
        repeats = [word for word, count in word_counts.items() if count > 1]
        repeats.sort()
        yield from (f'repeated word {word}' for word in repeats)

    def check_symmetry(self):
        grid = self.grid
        if grid.width != grid.height:
            yield 'not square'
            return
        x_limit = (grid.width + 1) // 2
        for x1 in range(x_limit):
            y_limit = grid.height if x1*2 < grid.width-1 else (grid.height+1)//2
            for y1 in range(y_limit):
                is_block1 = grid[x1, y1] is None
                x2 = grid.width - x1 - 1
                y2 = grid.height - y1 - 1
                is_block2 = grid[x2, y2] is None
                if is_block1 != is_block2:
                    yield (f'symmetry broken at {(x1 + 1, y1 + 1)} and '
                           f'{(x2 + 1, y2 + 1)}')

    @property
    def shape_counts(self):
        return Counter(block.shape
                       for block in self.blocks
                       if block.shape is not None)

    @property
    def shape_blocks(self):
        d = defaultdict(list)
        for block in self.blocks:
            if block.shape is not None:
                d[block.shape].append(block)
        return d

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

    @property
    def face_colour(self):
        return self.blocks[0].face_colour

    @face_colour.setter
    def face_colour(self, face_colour):
        for block in self.blocks:
            block.face_colour = face_colour

    def build_clues(self, document: QTextDocument, show_link=True):
        cursor = QTextCursor(document)
        cursor.movePosition(cursor.End)

        font_size = document.defaultFont().pixelSize()
        padding = font_size // 5
        document.setDefaultStyleSheet(f"""\
h1 {{text-align: center}}
hr.footer {{line-height:10px}}
p.footer {{page-break-after: always}}
td {{padding: {padding} }}
td.num {{text-align: right; background: {self.face_colour.name()}}}
a {{color: black}}
""")
        across_table = build_clue_table(self.across_clues)
        down_table = build_clue_table(self.down_clues)
        hints = self.build_hints()
        html = dedent(f"""\
            <h1>{escape(self.title)}</h1>
            <p>{escape(hints)}</p>
            <hr>
            <table>
            <tr><td>Across</td><td>Down</td></tr>
            <tr><td>
            {across_table}
            </td><td>
            {down_table}
            </td></tr>
            </table>
        """)
        if show_link:
            html += dedent("""\
                <hr class="footer">
                <p class="footer"><center><a href="https://donkirkby.github.io/four-letter-blocks"
                >https://donkirkby.github.io/four-letter-blocks</a></center></p>
                <p></p>
            """)
        cursor.insertHtml(html)
        cursor.movePosition(cursor.End)

    def build_hints(self):
        hints = self.HINT
        if self.use_suits:
            hints += ' '
            hints += self.SUIT_HINT
        hints += f' {len(self.blocks)} pieces.'
        return hints


def build_clue_table(clues: typing.Sequence[Clue]) -> str:
    rows = []
    for clue in clues:
        rows.append(f'<tr><td class="num">{clue.format_number()}.</td>'
                    f'<td>{escape(clue.format_text())}</td></tr>')
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


def parse_clues(text) -> typing.Dict[str, Clue]:
    clues: typing.Dict[str, Clue] = {}
    pairs = text.splitlines(keepends=False)
    for pair in pairs:
        try:
            word, clue_text = pair.split('-', maxsplit=1)
        except ValueError:
            continue
        word = word.strip()
        if word:
            clues[word] = Clue(clue_text.strip())
    return clues
