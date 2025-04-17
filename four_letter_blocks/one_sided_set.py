import math
import typing
from collections import Counter
from typing import TextIO

from PySide6.QtGui import QPainter
from mypy.checker import defaultdict

from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.puzzle import Puzzle, RotationsDisplay
from four_letter_blocks.puzzle_set import PuzzleSet


class OneSidedSet(PuzzleSet):
    def __init__(self,
                 *puzzles: Puzzle,
                 block_packer: BlockPacker | None = None,
                 packing_pages: TextIO | None = None,
                 start_hue: int = 0,
                 frame_lengths: typing.Sequence[int] = ()):
        self.frame_lengths = frame_lengths
        self.page_count = math.ceil(len(puzzles) / 2)
        self.page_index = 0
        self.page_packers: list[BlockPacker] = []
        sorted_puzzles = self.sort_puzzles(puzzles, packing_pages)
        if block_packer is None and self.page_packers:
            block_packer = self.page_packers[0]
        super().__init__(*sorted_puzzles,
                         block_packer=block_packer,
                         start_hue=start_hue)

    def sort_puzzles(self, puzzles, packing_pages) -> list[Puzzle]:
        if packing_pages is None:
            sorted_puzzles = puzzles
        else:
            packing_lines: list[str] = []
            sorted_puzzles = []
            seen_titles = set()
            for line in packing_pages:
                if line.startswith('type:'):
                    set_type = line[5:].strip()
                    if set_type != 'OneSidedSet':
                        raise ValueError(
                            f'Expected type OneSidedSet, but found {set_type}.')
                elif line.startswith('title:'):
                    title = line[6:].strip()
                    if title in seen_titles:
                        raise ValueError(f'Duplicate puzzle title: {title}.')
                    seen_titles.add(title)
                    for puzzle in puzzles:
                        if puzzle.title == title:
                            sorted_puzzles.append(puzzle)
                            break
                    else:
                        raise ValueError(f'Puzzle title not found: {title}.')
                else:
                    line = line.strip()
                    if line:
                        packing_lines.append(line)
                    elif packing_lines:
                        packing_text = '\n'.join(packing_lines)
                        page_packer = BlockPacker(start_text=packing_text)
                        self.page_packers.append(page_packer)
        return sorted_puzzles

    def pack_puzzles(self):
        page_puzzles = self.puzzles[self.page_index * 2: self.page_index * 2 + 2]
        shape_counts = Counter()
        for puzzle in page_puzzles:
            puzzle.rotations_display = RotationsDisplay.FRONT
            shape_counts += puzzle.shape_counts

        packed_shape_counts = Counter()
        for block in self.block_packer.create_blocks():
            rotated_shape = block.rotated_shape
            packed_shape_counts[rotated_shape] += 1

        required_shape_counts = shape_counts - packed_shape_counts
        self.block_packer.required_shape_counts = required_shape_counts
        self.block_packer.are_partials_saved = False
        # Current success is either use all shape counts or fill all space.
        # Distinguish between target shape counts and required shape counts.
        # self.block_packer.is_tracing = True
        is_filled = self.block_packer.fill()
        self.block_packer.sort_blocks()
        # print()
        # print(self.block_packer.display())
        if not is_filled:
            raise RuntimeError('Failed to pack puzzles.')
        shape_sources = defaultdict(list)
        for puzzle in page_puzzles:
            for block in puzzle.blocks:
                block.tab_count = 1
                rotated_shape = block.rotated_shape
                shape_sources[rotated_shape].append(block)
        for block in self.block_packer.create_blocks():
            rotated_shape = block.rotated_shape
            shape_source = shape_sources[rotated_shape]
            source_block = shape_source.pop()
            source_block.x = block.x
            source_block.y = block.y
            self.front_blocks[rotated_shape].append(source_block)

    def draw_cuts(self, painter, nick_radius=0):
        super().draw_cuts(painter, nick_radius)
        self.draw_black_square_cuts(painter, nick_radius)

    def draw_front(self, painter: QPainter) -> None:
        super().draw_front(painter)
        self.draw_black_squares(painter)