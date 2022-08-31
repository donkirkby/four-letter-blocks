import math
import typing
from collections import Counter, defaultdict
from collections.abc import Iterable

from PySide6.QtGui import QPainter, QColor

from four_letter_blocks.block import Block
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.line_deduper import LineDeduper
from four_letter_blocks.puzzle import Puzzle


class PuzzleSet:
    def __init__(self, *puzzles: Puzzle, block_packer: BlockPacker = None):
        self.puzzles = puzzles
        self.shape_counts: typing.Counter[str] = Counter()
        if block_packer:
            self.block_packer = block_packer
        else:
            self.block_packer = BlockPacker(16, 20,  # Game Crafter cutout size
                                            tries=10_000)
        self.front_blocks: typing.Dict[
            str,
            typing.List[typing.Optional[Block]]] = defaultdict(list)
        self.back_blocks: typing.Dict[
            str,
            typing.List[typing.Optional[Block]]] = defaultdict(list)

        total_counts = Counter()
        max_counts = Counter()
        max_puzzles = {}  # {combo: index}
        source_puzzles = defaultdict(list)  # {combo: [index]}
        combos = {'J': 'JL', 'L': 'JL', 'S': 'SZ', 'Z': 'SZ'}
        self.pairs = {}
        for pair in combos.values():
            first, last = pair
            self.pairs[first] = last
            self.pairs[last] = first
        for i, puzzle in enumerate(self.puzzles):
            puzzle_counts = Counter()
            for label, count in puzzle.shape_counts.items():
                combo = combos.get(label, label)
                puzzle_counts[combo] += count
                if combo != label:
                    puzzle_counts[label] += count
            total_counts += puzzle_counts
            for combo, count in puzzle_counts.items():
                source_puzzles[combo].append(i)
                if count > max_counts[combo]:
                    max_counts[combo] = count
                    max_puzzles[combo] = i
        all_combos = set(combos)
        all_combos.update(combos.values())
        all_combos.update(total_counts)
        extras = []
        for combo in sorted(all_combos):
            total_count = total_counts[combo]
            max_count = max_counts[combo]
            mirror = self.pairs.get(combo)
            if mirror is None:
                extra = 2*max_count - total_count
                if extra > 0:
                    extras.append(f'{combo}: {extra}({max_puzzles[combo]+1})')
                elif total_count % 2 != 0:
                    extras.append(f'{combo}: 1')
                if len(combo) == 1:
                    self.shape_counts[combo] = max(math.ceil(total_count/2),
                                                   max_count)
            else:
                full_combo = combos[combo]
                max_count = max_counts[full_combo]
                mirror_count = total_counts[mirror]
                extra = total_count - mirror_count
                if extra > 0:
                    extras.append(f'{combo}: {extra}')
                if combo < mirror:
                    self.shape_counts[combo] = max(total_count,
                                                   mirror_count,
                                                   max_count)

        for combo in all_combos:
            if len(combo) > 1:
                continue
            total_count = total_counts[combo]
            front_shape = combo
            back_shape = self.pairs.get(front_shape, front_shape)
            if front_shape == back_shape:
                front_count = math.ceil(total_count/2)
                back_count = total_count - front_count
                max_count = max_counts[front_shape]
            elif front_shape > back_shape:
                continue
            else:
                front_count = total_count
                back_count = total_counts[back_shape]
                max_count = max_counts[front_shape+back_shape]
            block_count = max(front_count, back_count, max_count)
            front_shape_blocks = [None] * block_count
            back_shape_blocks = [None] * block_count
            self.front_blocks[front_shape] = front_shape_blocks
            self.back_blocks[back_shape] = back_shape_blocks
            puzzle_counts = [(len(puzzle.shape_blocks[front_shape]) +
                              len(puzzle.shape_blocks[back_shape]),
                              i)
                             for i, puzzle in enumerate(self.puzzles)]
            puzzle_counts.sort(reverse=True)
            is_top = False
            for _, puzzle_index in puzzle_counts:
                is_top = not is_top
                puzzle = self.puzzles[puzzle_index]
                front_source = puzzle.shape_blocks[front_shape]
                if front_shape == back_shape:
                    back_source = front_source
                else:
                    back_source = puzzle.shape_blocks[back_shape]
                if is_top:
                    targets = range(block_count)
                else:
                    targets = range(block_count-1, -1, -1)
                for target in targets:
                    front = front_shape_blocks[target]
                    back = back_shape_blocks[target]
                    side = None
                    if front is not None:
                        if back is None:
                            side = 'B'
                    elif back is not None:
                        side = 'F'
                    elif len(front_source) >= len(back_source):
                        side = 'F'
                    else:
                        side = 'B'
                    if side == 'F' and front_source:
                        front_shape_blocks[target] = front_source.pop()
                    elif side == 'B' and back_source:
                        back_shape_blocks[target] = back_source.pop()
                if front_source or back_source:
                    raise RuntimeError("Blocks wouldn't fit.")

        if extras:
            self.block_summary = 'Extras: ' + ', '.join(extras)
        else:
            self.block_summary = ''
        self.block_packer.fill(self.shape_counts)
        size_pairs = [(puzzle.grid.width, i)
                      for i, puzzle in enumerate(self.puzzles)]
        size_pairs.sort()
        sizes = {size for size, i in size_pairs}
        standard_colours = {7: (120, 30),
                            9: (0, 0),
                            11: (60, 30),
                            13: (30, 30),
                            15: (0, 30)}
        unknown_sizes = sizes.difference(standard_colours)
        if unknown_sizes or len(sizes) != len(self.puzzles):
            angle = 360 / (len(self.puzzles)-1)
            for i, (width, puzzle_index) in enumerate(size_pairs):
                puzzle = self.puzzles[puzzle_index]
                if i == 0:
                    hue = saturation = 0
                else:
                    hue = 360 - i*angle
                    saturation = 30
                value = 255
                colour = QColor.fromHsv(hue, saturation, value)
                puzzle.face_colour = colour
        else:
            for (width, puzzle_index) in size_pairs:
                puzzle = self.puzzles[puzzle_index]
                hue, saturation = standard_colours[puzzle.grid.width]
                value = 255
                colour = QColor.fromHsv(hue, saturation, value)
                puzzle.face_colour = colour

    @property
    def square_size(self) -> int:
        return self.puzzles[0].square_size

    @square_size.setter
    def square_size(self, square_size: int):
        for puzzle in self.puzzles:
            puzzle.square_size = square_size

    def display_blocks(self,
                       block_packer: BlockPacker,
                       blocks: typing.Dict[str, typing.List[Block]],
                       x_offset: int = 0) -> Iterable[Block]:
        square_size = self.square_size
        positions = block_packer.positions
        for shape, shape_blocks in blocks.items():
            shape_positions = positions[shape][:]
            for block in shape_blocks:
                x, y, rotation = shape_positions.pop()
                x += x_offset
                if block is None:
                    continue
                block.set_display((x+0.5)*square_size, (y+0.5)*square_size, rotation)
                yield block

    def draw_cuts(self, painter, nick_radius=0):
        square_size = self.square_size
        blocks = self.block_packer.create_blocks()
        for block in blocks:
            for square in block.squares:
                square.size = square_size
                square.x = (square.x + 0.5) * square_size
                square.y = (square.y + 0.5) * square_size
            block.border_colour = Block.CUT_COLOUR
            block.draw_outline(painter, nick_radius)

    def draw_front(self,
                   painter: typing.Union[QPainter, LineDeduper],
                   x_offset: int = 0):
        for block in self.display_blocks(self.block_packer,
                                         self.front_blocks,
                                         x_offset):
            block.draw(painter, use_text=False)

    def draw_back(self,
                  painter: typing.Union[QPainter, LineDeduper],
                  x_offset: int = 0):
        block_packer = self.block_packer.flip()
        for block in self.display_blocks(block_packer,
                                         self.back_blocks,
                                         x_offset):
            block.draw(painter, use_text=False)
