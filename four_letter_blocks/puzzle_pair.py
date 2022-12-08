import typing
from collections import Counter

from PySide6.QtCore import QPoint, QRectF
from PySide6.QtGui import QPainter, QColor, QPainterPath, QBrush, \
    QRadialGradient, QConicalGradient

from four_letter_blocks.block import Block
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.clue_painter import CluePainter
from four_letter_blocks.line_deduper import LineDeduper
from four_letter_blocks.puzzle import Puzzle, RotationsDisplay
from four_letter_blocks.puzzle_set import PuzzleSet
from four_letter_blocks.square import Square


class PuzzlePair(PuzzleSet):
    LINK_TEXT = 'https://donkirkby.github.io/four-letter-blocks'

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
        self.set_face_colours()

    # noinspection DuplicatedCode
    def draw_front(self,
                   painter: typing.Union[QPainter, LineDeduper],
                   font_size: float | None = None) -> QRectF:
        front_puzzle, back_puzzle = self.puzzles
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

    def draw_front_blocks(self, painter: typing.Union[QPainter, LineDeduper]):
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
                  painter: typing.Union[QPainter, LineDeduper],
                  font_size: float | None = None):
        front_puzzle, back_puzzle = self.puzzles
        grid_rect = self.draw_header(painter, back_puzzle, font_size)
        self.draw_clues(painter, grid_rect, back_puzzle, font_size)
        offset = self.square_size / 2
        painter.translate(grid_rect.left() - offset,
                          grid_rect.top() - offset)
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
            if self.can_draw_block(block):
                block.draw(painter, is_packed=True)

    def draw_cuts(self,
                  painter: QPainter | LineDeduper,
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
        font.setPixelSize(font_size * 1.5)
        painter.setFont(font)
        CluePainter.draw_text(grid_rect,
                              puzzle.title,
                              painter,
                              is_centred=True,
                              is_dry_run=is_dry_run)

        font.setPixelSize(font_size)
        painter.setFont(font)
        hints = puzzle.build_hints()
        CluePainter.draw_text(grid_rect,
                              hints,
                              painter,
                              is_dry_run=is_dry_run)

        font.setPixelSize(font_size/2)
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
        margin = window.width() / 55
        clue_painter = CluePainter(puzzle,
                                   font_size=font_size,
                                   margin=margin)
        font = painter.font()
        font.setPixelSize(font_size)
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

    def draw_background_tile(self, painter: QPainter):
        background: QColor = painter.background().color()
        dark, light = self.get_target_colours(background, shift=0.75)
        window = painter.window()
        size = window.width()
        target = window.adjusted(0, 0, -size/2, -size/2)
        target.translate(size/2, size/2)
        x0 = window.left() + window.width()/2
        y0 = window.top() + window.height()/2
        path = QPainterPath(QPoint(x0, y0))
        path.arcTo(x0-size/4, y0-size/2, size/2, size/2, -90, 180)
        PuzzlePair.draw_background_tail(painter, light, background)

        painter.rotate(180)
        painter.translate(-window.width(), -window.height())
        PuzzlePair.draw_background_tail(painter, dark, background)
        gradient = QRadialGradient(x0, y0-size/4, size/4)
        gradient.setStops(((0, dark), (1, background)))
        painter.fillPath(path, QBrush(gradient))

        painter.rotate(180)
        painter.translate(-window.width(), -window.height())
        gradient.setStops(((0, light), (1, background)))
        painter.fillPath(path, QBrush(gradient))

    @staticmethod
    def draw_background_tail(painter: QPainter, ridge: QColor, edge: QColor):
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
