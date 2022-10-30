import math
import typing
from collections import Counter

from PySide6.QtCore import QRect, QPoint
from PySide6.QtGui import QPainter, QColor, QPainterPath, QBrush, \
    QRadialGradient, QConicalGradient, QPixmap, QTransform

from four_letter_blocks.block import Block
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.clue_painter import CluePainter
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
                   font_size: float | None = None):
        front_puzzle, back_puzzle = self.puzzles
        grid_rect = self.build_grid_rect(painter)
        self.draw_clues(painter, grid_rect, front_puzzle, font_size)
        self.set_grid_viewport(painter)
        self.draw_front_blocks(painter)

    def set_grid_viewport(self, painter):
        grid_rect = self.build_grid_rect(painter)
        painter.translate(grid_rect.left() - self.square_size / 2,
                          grid_rect.top() - self.square_size / 2)

    def build_grid_rect(self, painter):
        grid_size = self.puzzles[0].grid.width
        grid_rect = QRect(0,
                          0,
                          self.square_size * grid_size,
                          self.square_size * grid_size)
        margin = painter.window().width() / 55
        grid_rect.moveBottom(painter.window().height() - 1.7 * margin)
        grid_rect.moveLeft((painter.window().width() - grid_rect.width()) / 2)
        return grid_rect

    def draw_front_blocks(self, painter: typing.Union[QPainter, LineDeduper]):
        super().draw_front(painter)
        block = Block(Square(' '))
        block.squares[0].size = self.square_size
        block.face_colour = QColor('black')

        for x, y in self.black_positions:
            block.x = self.square_size * (x + 0.5)
            block.y = self.square_size * (y + 0.5)
            block.draw(painter, is_packed=True)

    def draw_back(self,
                  painter: typing.Union[QPainter, LineDeduper],
                  font_size: float | None = None):
        front_puzzle, back_puzzle = self.puzzles
        grid_rect = self.build_grid_rect(painter)
        self.draw_clues(painter, grid_rect, back_puzzle, font_size)
        self.set_grid_viewport(painter)
        self.draw_back_blocks(painter)

    def draw_back_blocks(self, painter: typing.Union[QPainter, LineDeduper]):
        super().draw_back(painter)
        grid_size = self.puzzles[0].grid.width
        block = Block(Square(' '))
        block.squares[0].size = self.square_size
        block.face_colour = QColor('black')

        for x, y in self.black_positions:
            block.x = self.square_size * (grid_size - x - 0.5)
            block.y = self.square_size * (y + 0.5)
            block.draw(painter, is_packed=True)

    def draw_cuts(self, painter, nick_radius=0):
        self.set_grid_viewport(painter)
        super().draw_cuts(painter, nick_radius)
        block = Block(Square(' '))
        block.squares[0].size = self.square_size
        block.border_colour = Block.CUT_COLOUR
        block.tab_count = 2

        for x, y in self.black_positions:
            block.x = self.square_size * (x + 0.5)
            block.y = self.square_size * (y + 0.5)
            block.draw_outline(painter, nick_radius)

    @staticmethod
    def draw_clues(painter: QPainter,
                   grid_rect: QRect,
                   puzzle: Puzzle,
                   font_size: float | None = None):
        if font_size is None:
            font_size = painter.window().height()/16
        margin = painter.window().width()/55
        clue_painter = CluePainter(puzzle,
                                   font_size=font_size,
                                   margin=margin)
        font = painter.font()
        font.setPixelSize(font_size)
        painter.setFont(font)
        line_height = clue_painter.find_text_height('X', painter)
        across_rect = QRect(margin,
                            margin,
                            grid_rect.left() - 2*margin,
                            painter.window().height() - 2*margin)
        painter.drawText(across_rect, 'Across')
        across_rect.adjust(0, line_height, 0, 0)
        clue_count = clue_painter.draw_clues(painter,
                                             puzzle.across_clues,
                                             across_rect)

        across_rect = QRect(grid_rect.left(),
                            margin,
                            grid_rect.width()//2 - margin,
                            grid_rect.top() - 2*margin)
        clue_count += clue_painter.draw_clues(
            painter,
            puzzle.across_clues[clue_count:],
            across_rect)

        down_rect = QRect(grid_rect.left() + grid_rect.width()//2,
                          margin,
                          grid_rect.width()//2 - margin,
                          grid_rect.top() - 2*margin)
        painter.drawText(down_rect, 'Down')
        down_rect.adjust(0, line_height, 0, 0)
        clue_count = clue_painter.draw_clues(painter,
                                             puzzle.down_clues,
                                             down_rect)
        down_rect = QRect(grid_rect.right()+margin,
                          margin,
                          painter.window().width()-grid_rect.right() - 2*margin,
                          painter.window().height() - 2*margin)
        clue_count += clue_painter.draw_clues(
            painter,
            puzzle.down_clues[clue_count:],
            down_rect)

    @staticmethod
    def draw_back_tile(painter: QPainter):
        background: QColor = painter.background().color()
        value_diff = (255 - background.value()) * 0.25
        light = QColor.fromHsv(background.hsvHue(),
                               background.hsvSaturation(),
                               background.value() + value_diff)
        dark = QColor.fromHsv(background.hsvHue(),
                              background.hsvSaturation(),
                              background.value() - value_diff)
        window = painter.window()
        size = window.width()
        target = window.adjusted(0, 0, -size/2, -size/2)
        target.translate(size/2, size/2)
        x0 = window.left() + window.width()/2
        y0 = window.top() + window.height()/2
        path = QPainterPath(QPoint(x0, y0))
        path.arcTo(x0-size/4, y0-size/2, size/2, size/2, -90, 180)
        PuzzlePair.draw_back_tail(painter, light, background)

        painter.rotate(180)
        painter.translate(-window.width(), -window.height())
        PuzzlePair.draw_back_tail(painter, dark, background)
        gradient = QRadialGradient(x0, y0-size/4, size/4)
        gradient.setStops(((0, dark), (1, background)))
        painter.fillPath(path, QBrush(gradient))

        painter.rotate(180)
        painter.translate(-window.width(), -window.height())
        gradient.setStops(((0, light), (1, background)))
        painter.fillPath(path, QBrush(gradient))

    @staticmethod
    def draw_back_tail(painter: QPainter, ridge: QColor, edge: QColor):
        window = painter.window()
        edge_value = edge.value()
        ridge_value = ridge.value()
        step_count = 100
        for step in range(-step_count, step_count):
            progress = step/step_count
            size = painter.window().width()
            x0 = window.left() + window.width()/2
            gap = size/4*(1 + progress)
            y0 = window.top() + window.height()/2 + gap
            path = QPainterPath(QPoint(x0, gap))
            path.arcTo(gap/2, gap, size-gap, size-gap, 90, 180)
            gradient = QConicalGradient(x0, y0, 90)
            step_value = ridge_value + (edge_value - ridge_value) * abs(progress)
            step_colour = QColor.fromHsv(edge.hsvHue(),
                                         edge.hsvSaturation(),
                                         step_value)
            gradient.setStops(((0, step_colour), (1, edge)))
            painter.fillPath(path, QBrush(gradient))

    @staticmethod
    def draw_back_pattern(painter: QPainter,
                          size: float,
                          x_offset: int = 0,
                          y_offset: int = 0):
        window = painter.window()
        viewport = painter.viewport()
        painter.eraseRect(window)
        tile_size = round(size)
        tile = QPixmap(tile_size, tile_size)
        tile_painter = QPainter(tile)
        tile_painter.setBackground(painter.background())
        tile_painter.eraseRect(tile_painter.window())
        try:
            PuzzlePair.draw_back_tile(tile_painter)
        finally:
            tile_painter.end()
        tiles = []
        for direction in range(4):
            rotated_tile = tile.transformed(QTransform().rotate(90*direction))
            tiles.append(rotated_tile)

        x_start = x_offset - math.ceil(x_offset/size)*size
        y_start = y_offset - math.ceil(y_offset/size)*size
        x_steps = math.ceil((window.width() - x_start) / size)
        y_steps = math.ceil((window.height() - y_start) / size)
        for j in range(x_steps):
            x = x_start + j*size
            for i in range(y_steps):
                y = y_start + i*size
                if i % 2 == 0:
                    direction = j % 2
                else:
                    direction = (3 - j % 2)
                source = tiles[direction]
                painter.drawPixmap(round(x), round(y), source)
        painter.setWindow(window)
        painter.setViewport(viewport)
