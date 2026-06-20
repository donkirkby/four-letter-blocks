import typing
from collections import Counter

from PySide6.QtGui import QPainter
from mypy.checker import defaultdict

from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.puzzle import Puzzle, RotationsDisplay
from four_letter_blocks.puzzle_set import PuzzleSet


class OneSidedSet(PuzzleSet):
    def __init__(self,
                 *puzzles: Puzzle,
                 block_packer: BlockPacker | None = None,
                 page_packers: typing.Sequence[BlockPacker] | None = None,
                 start_hue: int = 0,
                 set_options: dict | None = None,
                 frame_lengths: typing.Sequence[typing.Sequence[int]] = (),
                 puzzles_per_page: int = 2):
        """ Initialise a set of puzzles.

        The one-sided set was an experiment to leave the back side blank so that
        solvers could copy new puzzles onto the pieces with a dry-erase marker.
        It took too long to copy them.

        :param puzzles: The puzzles to pack.
        :param block_packer: The block packer to use.
        :param page_packers: The block packers to use for each travel page.
        :param start_hue: The hue of the first puzzle's face colour.
        :param set_options: Other options that can be set in a puzzle set file.
        :param frame_lengths: The number of squares in the frame segments:
            ((top, top, ...), (right, right, ...)).
        :param puzzles_per_page: The number of puzzles that will fit on a page.
        """
        self.frame_lengths = frame_lengths
        super().__init__(*puzzles,
                         block_packer=block_packer,
                         page_packers=page_packers,
                         start_hue=start_hue,
                         set_options=set_options,
                         puzzles_per_page=puzzles_per_page)

    def pack_puzzles(self):
        page_puzzles = self.puzzles[self.page_index * 2: self.page_index * 2 + 2]
        if self.page_packers:
            self.block_packer = self.page_packers[self.page_index]
        self.front_blocks.clear()

        shape_counts = Counter()
        for puzzle in page_puzzles:
            puzzle.rotations_display = RotationsDisplay.FRONT
            shape_counts += puzzle.shape_counts
        self.block_packer.required_shape_counts = shape_counts
        packed_shape_counts = self.block_packer.packed_shape_counts
        required_shape_counts = shape_counts - packed_shape_counts
        self.block_packer.required_shape_counts = required_shape_counts
        self.block_packer.are_partials_saved = False
        # Current success is either use all shape counts or fill all space.
        # Distinguish between target shape counts and required shape counts.
        self.block_packer.is_logging = True
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
        self.set_face_colours()
        self.pack_black_positions()

    def draw_cuts(self, painter, nick_radius=0):
        if self.page_index == 0:
            painter.translate(self.square_size / 2, self.square_size / 2)
        super().draw_cuts(painter, nick_radius)
        self.draw_black_square_cuts(painter, nick_radius)
        if self.page_index == 0:
            self.draw_frame(painter, nick_radius)
            painter.translate(-self.square_size / 2, -self.square_size / 2)

    def draw_frame(self, painter, nick_radius):
        top_frames, right_frames = self.frame_lengths
        first_block = self.puzzles[0].blocks[0]
        old_border_colour = first_block.border_colour
        first_block.border_colour = first_block.CUT_COLOUR
        old_pen = first_block.set_outline_pen(painter, nick_radius)
        old_tab_count = first_block.tab_count
        first_block.tab_count = 0
        size = first_block.squares[0].size
        full_width = (self.block_packer.width + 1) * size
        full_height = (self.block_packer.height + 1) * size
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

    def draw_front(self, painter: QPainter) -> None:
        if self.page_index == 0:
            painter.translate(self.square_size / 2, self.square_size / 2)
        super().draw_front(painter)
        self.draw_black_squares(painter)
        if self.page_index == 0:
            painter.translate(-self.square_size / 2, -self.square_size / 2)
