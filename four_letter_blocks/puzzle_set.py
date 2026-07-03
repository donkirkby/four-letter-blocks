import typing
from collections import Counter, defaultdict
from collections.abc import Iterable

import numpy as np
from PySide6.QtCore import QPoint
from PySide6.QtGui import QPainter, QColor, QPixmap, QPainterPath, \
    QBrush, QLinearGradient
from colorspacious import cspace_convert  # type:ignore[import]

from four_letter_blocks.block import Block, flipped_shapes
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.double_block_packer import DoubleBlockPacker
from four_letter_blocks.puzzle import Puzzle, draw_rotated_tiles, RotationsDisplay
from four_letter_blocks.square import Square
from four_letter_blocks.x_packer import XPacker


class PuzzleSet:
    LINK_TEXT = 'https://donkirkby.github.io/four-letter-blocks'

    def __init__(self,
                 *puzzles: Puzzle,
                 page_packers: typing.Sequence[XPacker] | None = None,
                 start_hue: int = 0,
                 set_options: dict | None = None,
                 frame_lengths: typing.Sequence[typing.Sequence[int]] = ()):
        """ Initialise a set of puzzles.

        :param puzzles: The puzzles to pack.
        :param page_packers: The block packers to use for each travel page.
        :param start_hue: The hue of the first puzzle's face colour.
        :param set_options: Other options that can be set in a puzzle set file.
        :param frame_lengths: The number of squares in the frame segments:
            ((top, top, ...), (right, right, ...)).
        :param puzzles_per_page: The number of puzzles that will fit on a page
            (both sides).
        """
        self.frame_lengths = frame_lengths
        set_options = set_options or {}
        self.puzzles = puzzles
        self.shape_counts: typing.Counter[str] = Counter()
        packing_pages = set_options.get('packing_pages', [])
        self.page_packers: list[XPacker] = []
        start_texts = [puzzle.format_blocks() for puzzle in puzzles]
        self.block_packer = DoubleBlockPacker(*start_texts)
        if packing_pages:
            for packing_page in packing_pages:
                self.page_packers.append(XPacker(start_text=packing_page))
        elif page_packers:
            self.page_packers = list(page_packers)
        else:
            # Game Crafter punchout size
            self.create_page_packers()
        self.page_count = len(self.page_packers)
        self.page_index = 0

        # { front_shape: [block] }
        self.front_blocks: typing.Dict[
            str,
            typing.List[Block | None]] = defaultdict(list)

        # { front_shape: [block] }
        self.back_blocks: typing.Dict[
            str,
            typing.List[Block | None]] = defaultdict(list)

        self.block_summary = ''
        self.start_hue: int = set_options.get('start_hue', start_hue)
        self.can_rotate: bool = set_options.get('can_rotate', True)
        self.black_positions: typing.List[typing.Tuple[int, int]] = []
        self.front_background = self.back_background = QColor('transparent')

    def create_page_packers(self):
        page_packer = XPacker(16, 20)
        page_packer.force_fours = False
        self.page_packers = [page_packer]

    def pack_black_positions(self):
        block_packer = self.page_packers[0]
        assert block_packer.state is not None
        black_coordinates = np.nonzero(block_packer.state < 2)
        black_rows, black_columns = black_coordinates
        self.black_positions = list(zip(black_columns, black_rows))

    def pack_puzzles(self) -> None:
        is_filled = self.block_packer.fill()
        if not is_filled:
            raise RuntimeError("Blocks wouldn't fit in puzzles.")

        front_puzzles: list[Puzzle] = []
        back_puzzles: list[Puzzle] = []
        for puzzle, target in zip(self.puzzles, self.block_packer.packing_targets):
            if target.is_front:
                puzzle.rotations_display = RotationsDisplay.FRONT
                source_packer = self.block_packer.front_packer
                side_blocks = self.front_blocks
                front_puzzles.append(puzzle)
            else:
                puzzle.rotations_display = RotationsDisplay.BACK
                source_packer = self.block_packer.back_packer
                side_blocks = self.back_blocks
                back_puzzles.append(puzzle)
            puzzle.blocks = Block.parse(target.display(source_packer),
                                        puzzle.grid)
            if target.is_front:
                self.shape_counts += puzzle.shape_counts
            for block in puzzle.blocks:
                shape = block.rotated_shape
                side_blocks[shape].append(block)

        page_packer = self.page_packers[0]
        if page_packer.packed_shape_counts != self.shape_counts:
            flipped_packer = page_packer.flip()
            if flipped_packer.packed_shape_counts == self.shape_counts:
                self.page_packers[0] = page_packer = flipped_packer

        page_packer.target_shape_counts = (self.shape_counts -
                                           page_packer.packed_shape_counts)
        if self.shape_counts.total() != 0:
            is_page_filled = page_packer.fill()
            if not is_page_filled:
                self.create_page_packers()
                page_packer = self.page_packers[0]
                page_packer.target_shape_counts = self.shape_counts
                is_page_filled = page_packer.fill()
            if not is_page_filled:
                raise RuntimeError("Blocks wouldn't fit in travel page.")

        unused_front_blocks = {
            shape: list(shape_blocks)
            for shape, shape_blocks in self.front_blocks.items()}
        unused_back_blocks = {
            shape: list(shape_blocks)
            for shape, shape_blocks in self.back_blocks.items()}
        block_count = sum(len(shape_blocks)
                          for shape, shape_blocks in self.front_blocks.items())
        block_count += sum(len(shape_blocks)
                           for shape, shape_blocks in self.back_blocks.items())
        self.block_summary = f'{block_count} blocks'
        for block in page_packer.create_blocks():
            shape = block.rotated_shape
            front_block = unused_front_blocks[shape].pop()
            assert front_block is not None
            front_block.set_display(block.x, block.y, 0)
            back_shape = flipped_shapes()[shape]
            back_block = unused_back_blocks[back_shape].pop()
            assert back_block is not None
            back_block.set_display(page_packer.width - block.x - block.width, block.y, 0)

        self.tab_count = 1
        self.set_face_colours(front_puzzles + back_puzzles, self.start_hue)
        if front_puzzles:
            self.front_background = front_puzzles[0].face_colour
        if back_puzzles:
            self.back_background = back_puzzles[0].face_colour
        self.pack_black_positions()

    @staticmethod
    def set_face_colours(puzzles: typing.Sequence[Puzzle], start_hue: int) -> None:
        if not puzzles:
            return

        size_pairs = [(puzzle.grid.width, i)
                      for i, puzzle in enumerate(puzzles)]
        size_pairs.sort()
        angle = 360 / len(puzzles)
        for i, (width, puzzle_index) in enumerate(size_pairs):
            puzzle = puzzles[puzzle_index]
            lightness = 77
            chroma = 20
            hue = (start_hue + i * angle) % 360
            rgb = cspace_convert((lightness, chroma, hue), "JCh", "sRGB255")
            colour = QColor.fromRgb(*rgb)
            puzzle.face_colour = colour

    @property
    def square_size(self) -> int:
        return self.puzzles[0].square_size

    @square_size.setter
    def square_size(self, square_size: int):
        for puzzle in self.puzzles:
            puzzle.square_size = square_size

    @property
    def tab_count(self) -> int:
        return self.puzzles[0].blocks[0].tab_count

    @tab_count.setter
    def tab_count(self, tab_count: int):
        for puzzle in self.puzzles:
            is_back = puzzle.rotations_display == RotationsDisplay.BACK
            for block in puzzle.blocks:
                block.tab_count = tab_count
                block.is_back = is_back

    def display_blocks(
            self,
            block_packer: BlockPacker,
            blocks: typing.Dict[str, typing.List[Block | None]]) -> Iterable[Block]:
        square_size = self.square_size
        can_rotate = all(len(shape) == 1 for shape in blocks)
        if can_rotate:
            positions = block_packer.positions
        else:
            positions = block_packer.rotated_positions
        for shape, shape_blocks in blocks.items():
            shape_positions = positions[shape][:]
            for block in shape_blocks:
                if can_rotate:
                    x, y, rotation = shape_positions.pop()
                else:
                    x, y = shape_positions.pop()
                    if shape == 'O':
                        rotation = 0
                    else:
                        rotation = int(shape[1])
                if block is None:
                    continue
                block.set_display((x+0.5)*square_size,
                                  (y+0.5)*square_size,
                                  rotation)
                yield block

    def draw_cuts(self, painter, nick_radius=0):
        square_size = self.square_size
        painter.translate(square_size / 2, square_size / 2)
        tab_count = self.tab_count
        blocks = self.page_packers[0].create_blocks()
        for block in blocks:
            block.tab_count = tab_count  # Need to copy tab_count to new blocks.
            for square in block.squares:
                square.size = square_size
                square.x = (square.x + 0.5) * square_size
                square.y = (square.y + 0.5) * square_size
            block.border_colour = Block.CUT_COLOUR
            if self.can_draw_block(block):
                block.draw_outline(painter, nick_radius)
        self.draw_black_square_cuts(painter, nick_radius)
        self.draw_frame(painter, nick_radius)
        painter.translate(-square_size / 2, -square_size / 2)

    def draw_front(self, painter: QPainter):
        painter.translate(self.square_size / 2, self.square_size / 2)
        block_packer = self.page_packers[0]
        for block in self.display_blocks(block_packer,
                                         self.front_blocks):
            if self.can_draw_block(block):
                block.draw(painter, is_packed=True)
        self.draw_black_squares(painter)
        painter.translate(-self.square_size / 2, -self.square_size / 2)

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def can_draw_block(self, block: Block) -> bool:
        return True

    def draw_back(self, painter: QPainter):
        painter.translate(self.square_size / 2, self.square_size / 2)
        block_packer = self.page_packers[0].flip()
        for block in self.display_blocks(block_packer, self.back_blocks):
            if self.can_draw_block(block):
                block.draw(painter, is_packed=True)
        self.draw_black_squares(painter, is_flipped=True)
        painter.translate(-self.square_size / 2, -self.square_size / 2)

    def draw_black_squares(self,
                           painter: QPainter,
                           is_flipped: bool = False) -> None:
        grid_size = self.page_packers[0].width
        block = Block(Square(' '))
        block.squares[0].size = self.square_size
        block.tab_count = self.tab_count  # Need to copy tab_counts to new block.
        block.is_back = is_flipped
        block.face_colour = QColor('black')
        for x, y in self.black_positions:
            if is_flipped:
                column = grid_size - x - 0.5
            else:
                column = x + 0.5
            block.x = self.square_size * column
            block.y = self.square_size * (y + 0.5)
            if self.can_draw_block(block):
                block.draw(painter, is_packed=True)

    def draw_black_square_cuts(self, painter, nick_radius):
        block = Block(Square(' '))
        block.squares[0].size = self.square_size
        block.border_colour = Block.CUT_COLOUR
        block.tab_count = self.tab_count  # Need to copy tab_counts to new block.
        for x, y in self.black_positions:
            block.x = self.square_size * (x + 0.5)
            block.y = self.square_size * (y + 0.5)
            if self.can_draw_block(block):
                block.draw_outline(painter, nick_radius)

    @staticmethod
    def draw_background(painter: QPainter, tile: QPixmap):
        for y in range(0, painter.window().height(), tile.height()):
            for x in range(0, painter.window().width(), tile.width()):
                painter.drawPixmap(x, y, tile)

    def draw_background_tile(self, painter) -> None:
        background: QColor = painter.background().color()
        dark, light = self.get_target_colours(background, shift=4)
        window = painter.window()
        size = window.width()
        for i in range(2):
            for j in range(2):
                if i % 2 == j % 2:
                    target_colour = light
                else:
                    target_colour = dark
                painter.translate(j*size/2, i*size/2)
                gradient = QLinearGradient(0, 0, 0, size/4)
                gradient.setStops(((0, background), (1, target_colour)))
                gradient.setSpread(gradient.Spread.ReflectSpread)
                for y in (0, size/2):
                    path = QPainterPath(QPoint(0, y))
                    path.lineTo(size/4, size/4)
                    path.lineTo(size/2, y)
                    path.lineTo(0, y)
                    painter.fillPath(path, QBrush(gradient))
                gradient = QLinearGradient(0, 0, size/4, 0)
                gradient.setStops(((0, background), (1, target_colour)))
                gradient.setSpread(gradient.Spread.ReflectSpread)
                for x in (0, size/2):
                    path = QPainterPath(QPoint(x, 0))
                    path.lineTo(size/4, size/4)
                    path.lineTo(x, size/2)
                    path.lineTo(x, 0)
                    painter.fillPath(path, QBrush(gradient))
                painter.translate(-j*size/2, -i*size/2)

    @staticmethod
    def get_target_colours(start: QColor, shift: float) -> tuple[QColor, QColor]:
        rgb = start.toRgb().toTuple()[:3]  # type: ignore
        lightness, chroma, hue = cspace_convert(rgb, 'sRGB255', 'JCh')
        high_lightness = lightness + shift
        if high_lightness > 100:
            raise ValueError(
                f'Start colour is too light, with lightness {lightness:0.2f}.')
        light_jch = [high_lightness, chroma, hue]
        low_lightness = lightness - shift
        if low_lightness < 0:
            raise ValueError(
                f'Start colour is too dark, with lightness {lightness:0.2f}.')
        dark_jch = [low_lightness, chroma, hue]
        light_rgb = cspace_convert(light_jch, 'JCh', 'sRGB255')
        dark_rgb = cspace_convert(dark_jch, 'JCh', 'sRGB255')
        light = QColor.fromRgb(*light_rgb)
        dark = QColor.fromRgb(*dark_rgb)
        if not (dark.isValid() and light.isValid()):
            raise ValueError('Start colour is invalid after shift.')
        return dark, light

    def draw_background_pattern(self,
                                painter: QPainter,
                                size: float,
                                x_offset: int = 0,
                                y_offset: int = 0):
        tile = self.create_background_tile(round(size),
                                           painter.background().color())
        draw_rotated_tiles(tile, painter, size, x_offset, y_offset)

    # Disable inspection and type check until issue PY-78964 is fixed.
    # noinspection PyInconsistentReturns
    def create_background_tile(self, tile_size: int,
                               background: QColor) -> QPixmap:  # type: ignore
        tile = QPixmap(tile_size, tile_size)
        tile_painter = QPainter(tile)
        tile_painter.setBackground(background)
        tile_painter.eraseRect(tile_painter.window())
        try:
            self.draw_background_tile(tile_painter)
        finally:
            tile_painter.end()
        return tile

    def draw_frame(self, painter, nick_radius):
        if not self.frame_lengths:
            return

        block_packer = self.page_packers[0]
        top_frames, right_frames = self.frame_lengths
        first_block = self.puzzles[0].blocks[0]
        old_border_colour = first_block.border_colour
        first_block.border_colour = first_block.CUT_COLOUR
        old_pen = first_block.set_outline_pen(painter, nick_radius)
        old_tab_count = first_block.tab_count
        first_block.tab_count = 0
        size = first_block.squares[0].size
        full_width = (block_packer.width + 1) * size
        full_height = (block_packer.height + 1) * size
        start_x = 0
        for top_frame in top_frames:
            if start_x == 0:
                # Top start
                first_block.draw_nicked_line(painter,
                                             nick_radius,
                                             size // 2, size // 2,
                                             0, size // 2)
                first_block.draw_nicked_line(painter,
                                             nick_radius,
                                             0, size // 2,
                                             0, 0)
                first_block.draw_nicked_line(painter,
                                             nick_radius,
                                             0, 0,
                                             size // 2, 0)

                # Bottom start
                first_block.draw_nicked_line(
                    painter,
                    nick_radius,
                    full_width - size // 2, full_height - size // 2,
                    full_width, full_height - size // 2)
                first_block.draw_nicked_line(
                    painter,
                    nick_radius,
                    full_width, full_height - size // 2,
                    full_width, full_height)
                first_block.draw_nicked_line(
                    painter,
                    nick_radius,
                    full_width, full_height,
                    full_width - size // 2, full_height)

            # Top
            end_x = start_x + top_frame
            first_block.draw_nicked_line(painter,
                                         nick_radius,
                                         start_x * size + size // 2, 0,
                                         end_x * size + size // 2, 0)
            first_block.draw_nicked_line(painter,
                                         nick_radius,
                                         end_x * size + size // 2, 0,
                                         end_x * size + size // 2, size // 2)

            # Bottom
            first_block.draw_nicked_line(
                painter,
                nick_radius,
                full_width - (start_x * size + size // 2), full_height,
                full_width - (end_x * size + size // 2), full_height)
            first_block.draw_nicked_line(
                painter,
                nick_radius,
                full_width - (end_x * size + size // 2), full_height,
                full_width - (end_x * size + size // 2), full_height - size // 2)
            start_x = end_x

        start_y = 0
        for right_frame in right_frames:
            if start_y == 0:
                # Right start
                first_block.draw_nicked_line(painter,
                                             nick_radius,
                                             full_width - size//2, size//2,
                                             full_width - size//2, 0)
                first_block.draw_nicked_line(painter,
                                             nick_radius,
                                             full_width - size//2, 0,
                                             full_width, 0)
                first_block.draw_nicked_line(painter,
                                             nick_radius,
                                             full_width, 0,
                                             full_width, size//2)

                # Left start
                first_block.draw_nicked_line(painter,
                                             nick_radius,
                                             size//2, full_height - size//2,
                                             size//2, full_height)
                first_block.draw_nicked_line(painter,
                                             nick_radius,
                                             size//2, full_height,
                                             0, full_height)
                first_block.draw_nicked_line(painter,
                                             nick_radius,
                                             0, full_height,
                                             0, full_height - size//2)

            # Top
            end_y = start_y + right_frame
            first_block.draw_nicked_line(
                painter,
                nick_radius,
                full_width, start_y * size + size//2,
                full_width, end_y * size + size//2)
            first_block.draw_nicked_line(
                painter,
                nick_radius,
                full_width, end_y * size + size//2,
                full_width - size//2, end_y * size + size//2)

            # Bottom
            first_block.draw_nicked_line(
                painter,
                nick_radius,
                0, full_height - (start_y * size + size//2),
                0, full_height - (end_y * size + size//2))
            first_block.draw_nicked_line(
                painter,
                nick_radius,
                0, full_height - (end_y * size + size//2),
                size//2, full_height - (end_y * size + size//2))
            start_y = end_y
        first_block.tab_count = old_tab_count
        first_block.border_colour = old_border_colour
        painter.setPen(old_pen)
