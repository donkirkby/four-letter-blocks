import typing
from collections import Counter

from PySide6.QtGui import QPainter, QColor

from four_letter_blocks.block import Block
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.line_deduper import LineDeduper
from four_letter_blocks.puzzle import Puzzle, RotationsDisplay
from four_letter_blocks.puzzle_set import PuzzleSet
from four_letter_blocks.square import Square


class PuzzlePair(PuzzleSet):
    def __init__(self,
                 front_puzzle: Puzzle,
                 back_puzzle: Puzzle,
                 block_packer: BlockPacker | None = None):
        super().__init__(front_puzzle, back_puzzle, block_packer=block_packer)
        self.black_positions: typing.List[typing.Tuple[int, int]] = []
        state = self.block_packer.display()
        for y, line in enumerate(state.splitlines()):
            for x, c in enumerate(line):
                if c in '.#':
                    self.black_positions.append((x, y))

    def pack_puzzles(self):
        front_puzzle, back_puzzle = self.puzzles
        front_puzzle.rotations_display = RotationsDisplay.FRONT
        self.shape_counts = front_puzzle.shape_counts
        packed_shape_counts = Counter({
            shape: len(positions)
            for shape, positions in self.block_packer.rotated_positions.items()})
        flipped_packer = self.block_packer.flip()
        flipped_shape_counts = Counter({
            shape: len(positions)
            for shape, positions in flipped_packer.rotated_positions.items()})
        if packed_shape_counts == self.shape_counts:
            pass
        elif flipped_shape_counts == self.shape_counts:
            self.block_packer = flipped_packer
        else:
            grid_size = front_puzzle.grid.width
            self.block_packer = BlockPacker(grid_size,
                                            grid_size,
                                            self.block_packer.tries)
            is_filled = self.block_packer.fill(self.shape_counts)
            if not is_filled:
                raise RuntimeError("Blocks didn't fit.")
        for block in front_puzzle.blocks:
            shape = block.shape
            rotation = block.shape_rotation
            if shape == 'O':
                front_combo = shape
            else:
                front_combo = f'{shape}{rotation}'
            self.front_blocks[front_combo].append(block)
        remaining_counts = Counter(self.shape_counts)
        for block in back_puzzle.blocks:
            shape = block.shape
            if shape == 'O':
                self.back_blocks[shape].append(block)
                remaining_counts[shape] -= 1
            else:
                front_shape = self.pairs.get(shape, shape)
                for rotation in range(4):
                    front_combo = f'{front_shape}{rotation}'
                    if remaining_counts[front_combo]:
                        self.back_blocks[shape].append(block)
                        remaining_counts[front_combo] -= 1
                        break

        for shape, count in remaining_counts.items():
            assert count == 0, (shape, count)
        front_puzzle.rotations_display = RotationsDisplay.OFF

    def draw_front(self,
                   painter: typing.Union[QPainter, LineDeduper],
                   x_offset: int = 0):
        super().draw_front(painter, x_offset)
        block = Block(Square(' '))
        block.squares[0].size = self.square_size
        block.face_colour = QColor('black')

        for x, y in self.black_positions:
            block.x = self.square_size * (x + x_offset + 0.5)
            block.y = self.square_size * (y + 0.5)
            block.draw(painter, is_packed=True)

    def draw_back(self,
                  painter: typing.Union[QPainter, LineDeduper],
                  x_offset: int = 0):
        super().draw_back(painter, x_offset)
        grid_size = self.puzzles[0].grid.width
        block = Block(Square(' '))
        block.squares[0].size = self.square_size
        block.face_colour = QColor('black')

        for x, y in self.black_positions:
            block.x = self.square_size * (grid_size - x + x_offset - 0.5)
            block.y = self.square_size * (y + 0.5)
            block.draw(painter, is_packed=True)

    def draw_cuts(self, painter, nick_radius=0):
        super().draw_cuts(painter, nick_radius)
        block = Block(Square(' '))
        block.squares[0].size = self.square_size
        block.border_colour = Block.CUT_COLOUR
        block.tab_count = 2

        for x, y in self.black_positions:
            block.x = self.square_size * (x + 0.5)
            block.y = self.square_size * (y + 0.5)
            block.draw_outline(painter, nick_radius)
