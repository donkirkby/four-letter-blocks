import math
import typing
from collections import Counter

from PySide6.QtCore import QPoint, QRectF
from PySide6.QtGui import QPainter, QColor, QPainterPath, Qt

from four_letter_blocks.block import Block
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.clue_overflow import ClueOverflow
from four_letter_blocks.clue_painter import CluePainter
from four_letter_blocks.puzzle import Puzzle, RotationsDisplay
from four_letter_blocks.puzzle_set import PuzzleSet
from four_letter_blocks.square import Square


class PuzzlePair(PuzzleSet):
    def __init__(self,
                 front_puzzle: Puzzle,
                 back_puzzle: Puzzle,
                 block_packer: BlockPacker | None = None,
                 start_hue: int = 0):
        super().__init__(front_puzzle,
                         back_puzzle,
                         block_packer=block_packer,
                         start_hue=start_hue)
        self.black_positions: typing.List[typing.Tuple[int, int]] = []
        state = self.block_packer.display()
        for y, line in enumerate(state.splitlines()):
            for x, c in enumerate(line):
                if c in '.#':
                    self.black_positions.append((x, y))
        self.slug_count = 1
        self.slug_index = 0

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
            self.block_packer = BlockPacker(
                grid_size,
                grid_size,
                self.block_packer.tries,
                split_row=self.block_packer.split_row)
            is_filled = self.block_packer.fill(Counter(self.shape_counts))
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
        self.set_face_colours()

    # noinspection DuplicatedCode
    def draw_front(self,
                   painter: QPainter,
                   font_size: float | None = None) -> QRectF:
        front_puzzle, back_puzzle = self.puzzles
        if font_size is None:
            font_size = painter.font().pixelSize()
        grid_rect = self.draw_header(painter, front_puzzle, font_size)
        self.draw_clues(painter, grid_rect, front_puzzle, font_size)
        offset = self.square_size / 2
        painter.translate(grid_rect.left() - offset,
                          grid_rect.top() - offset)
        self.draw_front_blocks(painter)
        painter.translate(offset - grid_rect.left(),
                          offset - grid_rect.top())
        return grid_rect

    def set_grid_viewport(self, painter):
        grid_rect = self.build_grid_rect(painter)
        painter.translate(grid_rect.left() - self.square_size / 2,
                          grid_rect.top() - self.square_size / 2)

    def build_grid_rect(self, painter) -> QRectF:
        window = painter.window()
        grid_size = self.puzzles[0].grid.width
        grid_rect = QRectF(0,
                           0,
                           self.square_size * grid_size,
                           self.square_size * grid_size)
        grid_rect.moveLeft((window.width() - grid_rect.width()) / 2)
        return grid_rect

    def draw_front_blocks(self, painter: QPainter):
        super().draw_front(painter)
        block = Block(Square(' '))
        block.squares[0].size = self.square_size
        block.face_colour = QColor('black')

        for x, y in self.black_positions:
            block.x = self.square_size * (x + 0.5)
            block.y = self.square_size * (y + 0.5)
            if self.can_draw_block(block):
                block.draw(painter, is_packed=True)

    # noinspection DuplicatedCode
    def draw_back(self,
                  painter: QPainter,
                  font_size: float | None = None):
        front_puzzle, back_puzzle = self.puzzles
        grid_rect = self.draw_header(painter, back_puzzle, font_size)
        self.draw_clues(painter, grid_rect, back_puzzle, font_size)
        offset = self.square_size / 2
        painter.translate(grid_rect.left() - offset,
                          grid_rect.top() - offset)
        self.draw_back_blocks(painter)

    def draw_back_blocks(self, painter: QPainter):
        super().draw_back(painter)
        grid_size = self.puzzles[0].grid.width
        block = Block(Square(' '))
        block.squares[0].size = self.square_size
        block.face_colour = QColor('black')

        for x, y in self.black_positions:
            block.x = self.square_size * (grid_size - x - 0.5)
            block.y = self.square_size * (y + 0.5)
            if self.can_draw_block(block):
                block.draw(painter, is_packed=True)

    def draw_cuts(self,
                  painter: QPainter,
                  nick_radius: int = 0,
                  header_fraction: float = 0.1):
        front_puzzle, back_puzzle = self.puzzles
        grid_size = front_puzzle.grid.width
        grid_length = grid_size * self.square_size
        window = painter.window()
        grid_rect = QRectF((window.width() - grid_length) / 2,
                           window.height()*header_fraction,
                           grid_length,
                           grid_length)
        shift = self.square_size / 2
        x_shift = grid_rect.left() - shift
        y_shift = grid_rect.top() - shift
        painter.translate(x_shift, y_shift)
        super().draw_cuts(painter, nick_radius)
        block = Block(Square(' '))
        block.squares[0].size = self.square_size
        block.border_colour = Block.CUT_COLOUR
        block.tab_count = 2

        for x, y in self.black_positions:
            block.x = self.square_size * (x + 0.5)
            block.y = self.square_size * (y + 0.5)
            if self.can_draw_block(block):
                block.draw_outline(painter, nick_radius)

        painter.translate(-x_shift, -y_shift)
        self.draw_boundary_cuts(painter, nick_radius)
    
    def draw_boundary_cuts(self,
                           painter: QPainter,
                           nick_radius: int = 0):
        pen = painter.pen()
        pen.setWidth(math.floor(self.square_size / 33))
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        pen.setColor(Block.CUT_COLOUR)
        painter.setPen(pen)

        width = painter.window().width()
        height = painter.window().height()
        margin = round(height / 66)  # Covers cutter drift

        block = Block(Square(' '))
        block.squares[0].size = self.square_size
        block.draw_nicked_line(painter,
                               nick_radius,
                               margin, margin,
                               width - margin, margin)
        block.draw_nicked_line(painter,
                               nick_radius,
                               margin, margin,
                               margin, height - margin)
        block.draw_nicked_line(painter,
                               nick_radius,
                               width - margin, margin,
                               width - margin, height - margin)
        block.draw_nicked_line(painter,
                               nick_radius,
                               margin, height - margin,
                               width - margin, height - margin)

    def draw_header(self,
                    painter: QPainter,
                    puzzle: Puzzle,
                    font_size: float | None = None,
                    is_dry_run: bool = False) -> QRectF:
        """ Draw the title and hints, return the grid rect below them. """
        window = painter.window()
        if font_size is None:
            font_size = window.height() / 16
        margin = window.width() / 55
        grid_rect = QRectF(self.build_grid_rect(painter))
        grid_rect.moveTop(margin)

        font = painter.font()
        font.setPixelSize(round(font_size * 1.5))
        painter.setFont(font)
        CluePainter.draw_text(grid_rect,
                              puzzle.title,
                              painter,
                              is_centred=True,
                              is_dry_run=is_dry_run)

        font.setPixelSize(round(font_size))
        painter.setFont(font)
        hints = puzzle.build_hints()
        CluePainter.draw_text(grid_rect,
                              hints,
                              painter,
                              is_dry_run=is_dry_run)

        font.setPixelSize(round(font_size/2))
        painter.setFont(font)
        CluePainter.draw_text(grid_rect,
                              self.LINK_TEXT,
                              painter,
                              is_centred=True,
                              is_dry_run=is_dry_run)
        grid_rect.translate(0, margin)
        grid_rect.setHeight(grid_rect.width())
        return grid_rect

    def draw_clues(self,
                   painter: QPainter,
                   grid_rect: QRectF,
                   puzzle: Puzzle,
                   font_size: float | None = None):
        window = painter.window()
        if font_size is None:
            font_size = window.height() / 16
        margin = round(window.width() / 55)
        clue_painter = CluePainter(puzzle,
                                   font_size=font_size,
                                   margin=margin)
        font = painter.font()
        font.setPixelSize(round(font_size))
        painter.setFont(font)
        clue_rects = [QRectF(margin,
                             margin,
                             grid_rect.left() - 2 * margin,
                             window.height() - 2 * margin),
                      QRectF(grid_rect.left(),
                             grid_rect.bottom() + margin,
                             (grid_rect.width() - margin) // 2,
                             window.height() - grid_rect.bottom() - 2 * margin),
                      QRectF(grid_rect.left() + (grid_rect.width() + margin)//2,
                             grid_rect.bottom() + margin,
                             (grid_rect.width() - margin) // 2,
                             window.height() - grid_rect.bottom() - 2 * margin),
                      QRectF(grid_rect.right() + margin,
                             margin,
                             window.width() - grid_rect.right() - 2 * margin,
                             window.height() - 2 * margin)]
        clue_groups = [('Across', puzzle.across_clues),
                       ('Down', puzzle.down_clues)]
        for group_name, clues in clue_groups:
            clue_count = 0
            while clue_rects:
                clue_rect = clue_rects[0]
                name_rect = QRectF(clue_rect)
                clue_painter.draw_text(clue_rect,
                                       group_name,
                                       painter,
                                       is_bold=True,
                                       is_dry_run=True)
                clue_count = clue_painter.draw_clues(painter,
                                                     clues,
                                                     clue_rect)
                if clue_count != 0:
                    clue_painter.draw_text(name_rect,
                                           group_name,
                                           painter,
                                           is_bold=True)
                    break

                clue_rects.pop(0)
            while clue_count < len(clues) and len(clue_rects) > 1:
                clue_rects.pop(0)
                clue_rect = clue_rects[0]
                clue_count += clue_painter.draw_clues(painter,
                                                      clues[clue_count:],
                                                      clue_rect)
            if clue_count < len(clues):
                raise ClueOverflow(clue_count, len(clues))

    def draw_background_tile(self, painter: QPainter):
        window = painter.window()

        total_shift = 4
        self.draw_background_tail(painter, total_shift, is_dark=True)

        painter.rotate(180)
        painter.translate(-window.width(), -window.height())
        self.draw_background_head(painter, total_shift, is_dark=False)
        self.draw_background_tail(painter, total_shift, is_dark=False)

        painter.rotate(180)
        painter.translate(-window.width(), -window.height())
        self.draw_background_head(painter, total_shift, is_dark=True)

    def draw_background_head(self,
                             painter: QPainter,
                             total_shift: float,
                             is_dark: bool):
        window = painter.window()
        x0 = round(window.left() + window.width()/2)
        y0 = round(window.top() + window.height()/2)
        size = window.width()
        background = painter.background().color()
        step_count = 100
        for step in range(step_count):
            progress = step/step_count
            dark, light = self.get_target_colours(
                background,
                shift=total_shift * progress)
            step_colour = dark if is_dark else light
            path = QPainterPath(QPoint(x0, round(y0-size/4)))
            path.arcTo(x0 - size / 4 * (1 - progress),
                       y0 - size / 4 * (2 - progress),
                       size / 2 * (1 - progress),
                       size / 2 * (1 - progress),
                       -90,
                       180)
            painter.fillPath(path, step_colour)

    def draw_background_tail(self,
                             painter: QPainter,
                             total_shift: float,
                             is_dark: bool):
        window = painter.window()
        background = painter.background().color()
        x0 = round(window.left() + window.width()/2)
        step_count = 100
        for step in range(-step_count, step_count):
            progress = step/step_count
            dark, light = self.get_target_colours(
                background,
                shift=total_shift * (1-abs(progress)))
            step_colour = dark if is_dark else light
            size = painter.window().width()

            # Gap from edge of window to outer edge of gradient.
            gap = round(size/4*(1 + progress))

            path = QPainterPath(QPoint(x0, gap))
            path.arcTo(gap/2, gap, size-gap, size-gap, 90, 180)
            painter.fillPath(path, step_colour)
