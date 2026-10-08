import math
import re
import typing
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum, auto
from html import escape
from itertools import chain
from operator import attrgetter
from pathlib import Path
from random import shuffle, randrange
from subprocess import run
from tempfile import NamedTemporaryFile
from textwrap import dedent

import numpy as np
from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter, QTextDocument, QTextCursor, QPixmap, \
    QTransform, QFont
from scipy.ndimage import label

from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.clue import Clue
from four_letter_blocks.grid import Grid
from four_letter_blocks.block import Block


class RotationsDisplay(Enum):
    OFF = auto()
    FRONT = auto()
    BACK = auto()


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
    is_packed: bool = False
    rotations_display: RotationsDisplay = RotationsDisplay.OFF
    _source_path: Path | None = None
    are_unkeyed_squares_allowed: bool = False

    @staticmethod
    def parse(source_file: typing.IO) -> 'Puzzle':
        title, grid_text, clues_text, blocks_text = split_sections(source_file)
        return Puzzle.parse_sections(title, grid_text, clues_text, blocks_text)

    @staticmethod
    def parse_path(source_path: Path) -> 'Puzzle':
        with source_path.open() as source_file:
            puzzle = Puzzle.parse(source_file)
            puzzle.source_path = source_path.absolute()
            return puzzle

    @staticmethod
    def parse_sections(
            title: str,
            grid_text: str,
            clues_text: str,
            blocks_text: str,
            old_clues: typing.Dict[str, Clue] | None = None,
            old_blocks: typing.List[typing.List[str]] | None = None) -> 'Puzzle':
        if old_clues is None:
            old_clues = {}
        grid = Grid(grid_text)
        parsed_clues = parse_clues(clues_text)
        for word, clue in parsed_clues.items():
            old_clues[word] = clue
        all_clues = {}
        blocks = Block.parse(blocks_text, grid, old_blocks)
        for block in blocks:
            for square in block.squares:
                if square.number is None:
                    continue
                for new_word in (square.across_word, square.down_word):
                    if new_word is None:
                        continue
                    old_clue = old_clues.get(new_word, Clue(''))
                    clue = parsed_clues.get(new_word, old_clue)
                    all_clues[new_word] = clue
        return Puzzle(title, grid, all_clues, blocks)

    def __post_init__(self):
        self.across_clues = []
        self.down_clues = []
        self.use_suits = 121 < self.grid.width * self.grid.height
        self.number_clues()

    @property
    def source_path(self) -> Path | None:
        return self._source_path

    @source_path.setter
    def source_path(self, source_path: Path):
        if source_path is not None and not source_path.is_absolute():
            raise ValueError('source_path must be an absolute path.')
        self._source_path = source_path

    def number_clues(self) -> None:
        self.across_clues.clear()
        self.down_clues.clear()
        references = {}  # {word: reference} e.g., {'FOO': '1 Across'}
        used_numbers: Counter[int|None] = Counter()  # {suit_slot: used_number}
        suits = list('CDHS')
        suit_order: list[None | str] = [None] * 4
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
        return 1  # No squares found, return default.

    @square_size.setter
    def square_size(self, value: int):
        if value <= 0:
            raise ValueError('Square size must be positive.')

        ratio = value / self.square_size
        all_squares = (square
                       for row in self.grid.squares
                       for square in row
                       if square is not None)
        for square in all_squares:
            if square is not None:
                square.size = round(value)
                square.x = round(square.x * ratio)
                square.y = round(square.y * ratio)

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
                    square_size: int | None = None,
                    row_index: int | None = None,
                    x: int = 0,
                    y: int = 0) -> int:
        """ Draw all blocks on a painter. Return the height of the image. """
        window_width = painter.window().width()
        if square_size is None:
            square_size = window_width // self.DEFAULT_ROW_LENGTH
        self.square_size = square_size
        gap = round(square_size / 2)
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
                block.draw(painter, is_packed=self.is_packed)
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
                    window_width: int | None = None,
                    square_size: int | None = None) -> typing.List[int]:
        """ Height needed to draw each row of blocks. """
        row_heights = []
        if square_size is None and window_width is not None:
            square_size = window_width // self.DEFAULT_ROW_LENGTH
        elif square_size is not None and window_width is None:
            window_width = square_size * self.DEFAULT_ROW_LENGTH
        elif window_width is None:
            square_size = self.square_size
            window_width = square_size * self.DEFAULT_ROW_LENGTH
        assert square_size is not None
        self.square_size = square_size
        gap = round(self.square_size / 2)
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
        unused_markers = (Block.UNUSED,
                          BlockPacker.BLOCK_CHARS[BlockPacker.UNUSED])
        for i, block in enumerate(self.blocks, start=BlockPacker.GAP + 1):
            if block.marker in unused_markers:
                block_letter = '?'
            else:
                block_letter = BlockPacker.BLOCK_CHARS[i]
            for square in block.squares:
                x = square.x
                y = square.y
                rows[y][x] = block_letter
        return '\n'.join(''.join(row) for row in rows)

    def format_deck(self) -> str:
        deck_entries: list[str] = []
        for y in range(self.grid.height):
            for x in range(self.grid.width):
                square = self.grid[x, y]
                if square is None:
                    continue

                for word, dx, dy in ((square.across_word, 1, 0),
                                     (square.down_word, 0, 1)):
                    if word is None:
                        continue

                    word_entries: list[str] = []
                    for i, letter in enumerate(word):
                        x2 = x + i*dx
                        y2 = y + i*dy
                        word_entries.append(f'{x2}_{y2}')
                        if letter != '.':
                            word_entries.append(f'={letter}')
                    deck_entries.append(' '.join(word_entries))
        return '\n'.join(deck_entries)

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
        warnings.extend(self.check_connection())
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
        repeats = [word
                   for word, count in word_counts.items()
                   if count > 1 and '.' not in word]
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

    def check_connection(self):
        grid = self.grid
        spaces = grid.space_flags
        space_array = np.zeros((grid.height + 2, grid.width + 2), np.short)
        space_array[1:-1, 1:-1] = spaces
        labelled_spaces, group_count = label(space_array)
        if 1 < group_count:
            group_starts: list[tuple[int, int]] = []
            for group_num in range(1, group_count+1):
                i_s, j_s = np.where(labelled_spaces == group_num)
                x = int(j_s[0])
                y = int(i_s[0])
                group_starts.append((x, y))
            group_starts.sort()
            squares_text = ', '.join(str(square) for square in group_starts)
            yield f'disconnected sections at {squares_text}'

        if not self.are_unkeyed_squares_allowed:
            horizontal_neighbour_count = (space_array[:,:-2] +
                                          space_array[:,1:-1] +
                                          space_array[:,2:])
            i_s, j_s = np.where(np.logical_and(horizontal_neighbour_count == 1,
                                               space_array[:, 1:-1]))
            unchecked_squares: set[tuple[int, int]] = set()
            for i, j in zip(i_s, j_s):
                unchecked_squares.add((int(j+1), int(i)))
            vertical_neighbour_count = (space_array[:-2,:] +
                                        space_array[1:-1,:] +
                                        space_array[2:,:])
            i_s, j_s = np.where(np.logical_and(vertical_neighbour_count == 1,
                                               space_array[1:-1, :]))
            for i, j in zip(i_s, j_s):
                unchecked_squares.add((int(j), int(i+1)))
            if unchecked_squares:
                squares_text = ', '.join(str(square)
                                         for square in sorted(unchecked_squares))
                yield f'unkeyed squares at {squares_text}'

    @property
    def shape_counts(self) -> typing.Counter[str]:
        if self.rotations_display == RotationsDisplay.OFF:
            return Counter(block.shape
                           for block in self.blocks
                           if block.shape is not None)
        counter: typing.Counter[str] = Counter()
        for block in self.blocks:
            if block.marker == Block.UNUSED:
                continue
            shape = block.shape
            rotation = block.shape_rotation
            if self.rotations_display == RotationsDisplay.BACK:
                rotation = -rotation % 4
                match shape:
                    case 'S':
                        shape = 'Z'
                    case 'Z':
                        shape = 'S'
                    case 'J':
                        shape = 'L'
                    case 'L':
                        shape = 'J'
            match shape:
                case None:
                    continue
                case 'I' | 'S' | 'Z':
                    shape = f'{shape}{rotation % 2}'
                case 'J' | 'L' | 'T':
                    shape = f'{shape}{rotation}'
            counter[shape] += 1
        return counter

    @property
    def flipped_shape_counts(self):
        shape_counts = self.shape_counts
        if self.rotations_display == RotationsDisplay.OFF:
            shape_counts['J'], shape_counts['L'] = (shape_counts['L'],
                                                    shape_counts['J'])
            shape_counts['S'], shape_counts['Z'] = (shape_counts['Z'],
                                                    shape_counts['S'])
            return shape_counts

        flipped_shapes = {'J': 'L',
                          'L': 'J',
                          'Z': 'S',
                          'S': 'Z'}
        flipped_shape_counts = Counter()
        for name, count in shape_counts.items():
            if len(name) == 1:
                flipped_shape_counts[name] = count
                continue
            shape_name, rotation = name
            flipped_shape = flipped_shapes.get(shape_name, shape_name)
            flipped_rotation = -int(rotation) % 4
            if flipped_shape in 'SZI':
                flipped_rotation = flipped_rotation % 2
            flipped_name = f'{flipped_shape}{flipped_rotation}'
            flipped_shape_counts[flipped_name] = count
        return flipped_shape_counts

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

    @property
    def font(self) -> QFont | None:
        return self.blocks[0].font

    @font.setter
    def font(self, font: QFont | None):
        for block in self.blocks:
            block.font = font

    def build_clues(self, document: QTextDocument, show_link=True):
        cursor = QTextCursor(document)
        cursor.movePosition(QTextCursor.MoveOperation.End)

        font_size = document.defaultFont().pixelSize()
        padding = font_size // 5
        document.setDefaultStyleSheet(dedent(f"""\
            h1 {{text-align: center}}
            hr.footer {{line-height:10px}}
            p.footer {{page-break-after: always}}
            td {{padding: {padding} }}
            td.num {{text-align: right}}
            a {{color: black}}
            """))
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
        cursor.movePosition(QTextCursor.MoveOperation.End)

    def build_hints(self):
        hints = self.HINT
        if self.use_suits:
            hints += ' '
            hints += self.SUIT_HINT
        hints += f' {len(self.blocks)} pieces.'
        return hints

    def generate(self, random_level: int = 2) -> 'Puzzle':
        with NamedTemporaryFile('w', suffix='.qxd', prefix='puzzle') as f:
            f.write(f'.RANDOM {random_level}\n')
            deck_text = self.format_deck()
            f.write(deck_text)
            f.flush()
            result = run(['qxw', '-b', f.name], capture_output=True)
            if result.stderr:
                raise RuntimeError('Qxw failed: ' + result.stderr.decode())

            new_grid = [list(line)
                        for line in self.format_grid().splitlines()]
            generated_text = result.stdout.decode()
            deck_words = deck_text.splitlines()
            for line in generated_text.splitlines():
                if line.startswith('#'):
                    continue
                word_label, word = line.split()
                i = int(word_label[1:])
                deck_word = deck_words[i]
                deck_letters = deck_word.split()
                for coordinates_text, letter in zip(deck_letters,
                                                    word):
                    x_text, y_text = coordinates_text.split('_')
                    x = int(x_text)
                    y = int(y_text)
                    new_grid[y][x] = letter
        new_grid_text = '\n'.join(''.join(row) for row in new_grid)
        new_puzzle = Puzzle.parse_sections(self.title,
                                           new_grid_text,
                                           self.format_clues(),
                                           self.format_blocks())
        return new_puzzle


def build_clue_table(clues: typing.Sequence[Clue]) -> str:
    rows = []
    for clue in clues:
        rows.append(f'<tr><td class="num">{clue.format_number()}.</td>'
                    f'<td>{escape(clue.format_text())}</td></tr>')
    return f'<table>{"".join(rows)}</table>'


def split_sections(source_file) -> typing.List[str]:
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


def draw_rotated_tiles(tile: QPixmap,
                       painter: QPainter,
                       size: float,
                       x_offset: float = 0,
                       y_offset: float = 0,
                       bounds: QRectF | None = None):
    """ Draw a tile, converted to four-fold rotational symmetry.

    Tile will be drawn throughout bounds, repeated every size pixels.
    Repetitions will be rotated, so the combined pattern has four-fold
    rotational symmetry.

    :param tile: image to rotate and tile
    :param painter: to draw tiles on, with background colour set to match tile
    :param size: width and height to repeat tile pattern
    :param x_offset: offset to a tile left. Tiles are also repeated to the left.
    :param y_offset: offset to a tile top. Tiles are also repeated above.
    :param bounds: area to draw tiles within. Defaults to painter.window().
    """
    if bounds is None:
        bounds = QRectF(painter.window())
        bounds.setRight(bounds.right() + 1)
    painter.eraseRect(bounds)
    tiles = []
    for direction in range(4):
        rotated_tile = tile.transformed(QTransform().rotate(90 * direction))
        tiles.append(rotated_tile)
    x_start = x_offset - math.ceil(x_offset / size) * size
    y_start = y_offset - math.ceil(y_offset / size) * size
    x_steps = math.ceil((bounds.width() - x_start) / size)
    y_steps = math.ceil((bounds.height() - y_start) / size)
    x_start += bounds.left()
    y_start += bounds.top()
    for j in range(x_steps):
        x = x_start + j * size
        if x + size <= bounds.right():
            source_width = round(size)
        else:
            source_width = round(bounds.right() - x)
        if x >= bounds.left():
            source_x = 0
        else:
            source_x = round(bounds.left() - x + 1)
            source_width -= source_x - 1
            x = bounds.left()
        for i in range(y_steps):
            y = y_start + i * size
            if y + size <= bounds.bottom():
                source_height = round(size)
            else:
                source_height = round(bounds.bottom() - y + 1)
            if y >= bounds.top():
                source_y = 0
            else:
                source_y = round(bounds.top() - y + 1)
                source_height -= source_y - 1
                y = bounds.top()
            if i % 2 == 0:
                direction = j % 2
            else:
                direction = (3 - j % 2)
            source = tiles[direction]
            painter.drawPixmap(round(x), round(y),
                               source,
                               source_x, source_y,
                               source_width, source_height)


def calculate_max_black(size: int) -> int:
    """ Default value for maximum number of black squares in a layout.

    1/6 of the grid.
    :param size: the width and height of the layouts
    """
    return size*size // 6

def count_layout_numbers(size: int, max_black: int = -1) -> int:
    """ Count how many layout numbers are possible for a size.

    A layout number chooses a location for each black square, or 0 to skip
    that black square. The locations are anywhere up to the middle square of the
    layout, because the second half is a mirror of the first half.

    :param size: the width and height of the layouts
    :param max_black: maximum number of black squares. Defaults to 1/6 of the
        grid if you pass in -1.
    """
    if max_black == -1:
        max_black = calculate_max_black(size)
    location_count = (size*size + 3) // 2
    return location_count ** (max_black//2)


def generate_layout(size: int, layout_number: int) -> str:
    """ Generate a layout for a given layout number.

    :param size: width and height of the layout.
    :param layout_number: layout number up to count_layout_numbers(size)
    :return: layout text with black squares placed according to the layout
    number. Some layout numbers are duplicates of other layout numbers, and some
    layouts are invalid. Check for valid layouts with Puzzle.check_style().
    """
    location_count = (size*size + 3) // 2
    layout = [['.'] * size for _ in range(size)]
    location_choices = layout_number
    while location_choices:
        i = location_choices % location_count - 1
        if 0 <= i:
            x = i % size
            y = i // size
            x2 = size - 1 - x
            y2 = size - 1 - y
            layout [y][x] = '#'
            layout [y2][x2] = '#'
        location_choices = location_choices // location_count
    grid_text = '\n'.join(''.join(row) for row in layout)

    return grid_text

    # puzzle = Puzzle.parse_sections('', grid_text, '', '')
    # if not any(puzzle.check_word_length()):
    #     return grid_text
    #
    # return generate_layout(size, layout_number + 1)


def main():
    size = 7
    success_count = 0
    max_black = calculate_max_black(size)

    while True:
        max_black2 = randrange(max_black//2, max_black+1)
        layout_count = count_layout_numbers(size, max_black2)
        layout_number = randrange(layout_count)
        grid_text = generate_layout(size, layout_number)
        puzzle = Puzzle.parse_sections('', grid_text, '', '')
        warnings = puzzle.check_style()
        if not warnings:
            success_count += 1
            start_time = datetime.now()
            print(f'{success_count}: {layout_number} {start_time}')
            print(puzzle.format_grid())
            puzzle = puzzle.generate()
            # print(f'{i}: layout {layout_number}, max {max_black2} black, {len(warnings)} warnings.')
            print(datetime.now() - start_time)
            print(puzzle.format_grid())
            # print('\n  '.join(warnings))
            print()


if __name__ in ('__main__', '__live_coding__'):
    main()
