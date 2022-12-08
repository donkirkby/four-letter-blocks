import math

from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter, Qt

from four_letter_blocks.block import Block
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.clue_painter import CluePainter
from four_letter_blocks.line_deduper import LineDeduper
from four_letter_blocks.puzzle import Puzzle
from four_letter_blocks.puzzle_pair import PuzzlePair
from four_letter_blocks.square import Square


class BigPuzzlePair(PuzzlePair):
    def __init__(self,
                 front_puzzle: Puzzle,
                 back_puzzle: Puzzle,
                 block_packer: BlockPacker | None = None,
                 start_hue: int = 0):
        super().__init__(front_puzzle,
                         back_puzzle,
                         block_packer,
                         start_hue=start_hue)
        self.slug_count = 2

    def draw_header(self,
                    painter: QPainter,
                    puzzle: Puzzle,
                    font_size: float | None = None,
                    is_dry_run: bool = False) -> QRectF:
        if self.slug_index == 1:
            return self.draw_header2(painter, puzzle, font_size)

        # noinspection DuplicatedCode
        height = painter.window().height()
        width = painter.window().width()
        margin = round(height / 66)  # Covers cutter drift
        column_count = puzzle.grid.width
        row_count = math.floor(column_count/2)
        grid_height = row_count * self.square_size
        grid_width = column_count * self.square_size
        grid_rect = QRectF((width - grid_width)/2,
                           height - 2*margin - grid_height,
                           grid_width,
                           grid_height)

        font = painter.font()
        font.setPixelSize(font_size * 1.5)
        painter.setFont(font)
        header_rect = QRectF(2*margin, 2*margin,
                             width - 4*margin, grid_rect.top() - 2*margin)
        hints_rect = header_rect.adjusted(
            CluePainter.find_text_width(puzzle.title, painter) + margin, 0,
            0, 0)
        CluePainter.draw_text(header_rect, puzzle.title, painter)

        font.setPixelSize(font_size)
        painter.setFont(font)
        CluePainter.draw_text(hints_rect, puzzle.build_hints(), painter)

        clues_start = max(header_rect.top(), hints_rect.top()) + margin
        clues_width = (width - 4*margin) / 4 - margin
        clues_height = grid_rect.top() - clues_start - 2*margin

        clue_rect_template = QRectF(2*margin, clues_start, clues_width, clues_height)
        self.draw_header_clues(painter,
                               CluePainter(puzzle, font_size=font_size),
                               'Across',
                               puzzle.across_clues,
                               clue_rect_template,
                               margin)
        return grid_rect

    def draw_header2(self,
                     painter: QPainter,
                     puzzle: Puzzle,
                     font_size: float | None = None) -> QRectF:
        # noinspection DuplicatedCode
        height = painter.window().height()
        width = painter.window().width()
        margin = round(height / 66)  # Covers cutter drift
        column_count = puzzle.grid.width
        hidden_row_count = math.floor(column_count/2)
        hidden_height = hidden_row_count * self.square_size
        grid_width = column_count * self.square_size
        grid_rect = QRectF((width - grid_width) / 2,
                           2 * margin - hidden_height,
                           grid_width,
                           grid_width)

        font = painter.font()
        font.setPixelSize(font_size / 2)
        painter.setFont(font)
        painter.rotate(-90)
        frame_start = width - (width - grid_width) / 2
        link_height = CluePainter.find_text_height(self.LINK_TEXT, painter)
        link_start = (width + frame_start - margin - link_height) / 2
        link_rect = QRectF(hidden_height-grid_width-2*margin, link_start,
                           grid_width-hidden_height, width)
        CluePainter.draw_text(link_rect,
                              self.LINK_TEXT,
                              painter,
                              is_centred=True)
        painter.rotate(90)

        font.setPixelSize(font_size)
        painter.setFont(font)
        clue_start = grid_rect.bottom() + 2*margin
        clue_width = (width - 4*margin) / 4 - margin
        clue_height = height - clue_start - 2*margin
        clue_rect_template = QRectF(2*margin,
                                    clue_start,
                                    clue_width,
                                    clue_height)
        self.draw_header_clues(painter,
                               CluePainter(puzzle, font_size=font_size),
                               'Down',
                               puzzle.down_clues,
                               clue_rect_template,
                               margin)

        return grid_rect

    @staticmethod
    def draw_header_clues(painter,
                          clue_painter,
                          section_name,
                          clues,
                          clue_rect_template,
                          margin):
        clue_rect = QRectF(clue_rect_template)
        CluePainter.draw_text(clue_rect, section_name, painter, is_bold=True)
        clue_count = clue_painter.draw_clues(painter,
                                             clues,
                                             clue_rect)
        clue_rect_template.translate(clue_rect_template.width() + margin, 0)
        clue_rect = QRectF(clue_rect_template)
        clue_count += clue_painter.draw_clues(painter,
                                              clues[clue_count:],
                                              clue_rect)
        clue_rect_template.translate(clue_rect_template.width() + margin, 0)
        clue_rect = QRectF(clue_rect_template)
        clue_count += clue_painter.draw_clues(painter,
                                              clues[clue_count:],
                                              clue_rect)
        clue_rect_template.translate(clue_rect_template.width() + margin, 0)
        clue_rect = QRectF(clue_rect_template)
        clue_painter.draw_clues(painter,
                                clues[clue_count:],
                                clue_rect)

    def draw_clues(self,
                   painter: QPainter,
                   grid_rect: QRectF,
                   puzzle: Puzzle,
                   font_size: float | None = None):
        # Clues are part of header in this class.
        pass

    def can_draw_block(self, block: Block) -> bool:
        column_count = self.puzzles[0].grid.width
        row_count = math.floor(column_count/2)
        limit = row_count * self.square_size
        y = block.display_y
        if y is None:
            y = block.y
        if self.slug_index == 0:
            return y < limit
        return limit <= y

    def draw_cuts(self,
                  painter: QPainter | LineDeduper,
                  nick_radius: int = 0,
                  header_fraction: float = 0.1):
        super().draw_cuts(painter, nick_radius, header_fraction)

        pen = painter.pen()
        pen.setWidth(math.floor(self.square_size / 33))
        pen.setCapStyle(Qt.FlatCap)
        pen.setColor(Block.CUT_COLOUR)
        painter.setPen(pen)

        if self.slug_index == 1:
            self.draw_cuts2(painter, nick_radius)
            return
        width = painter.window().width()
        height = painter.window().height()
        margin = round(height / 66)  # Covers cutter drift
        column_count = self.puzzles[0].grid.width
        grid_width = column_count * self.square_size

        block = Block(Square(' '))
        block.squares[0].size = self.square_size
        block.draw_nicked_line(painter,
                               nick_radius,
                               margin, margin,
                               margin, height - 2*margin)
        block.draw_nicked_line(painter,
                               nick_radius,
                               margin, margin,
                               width - margin, margin)
        block.draw_nicked_line(painter,
                               nick_radius,
                               width - margin, margin,
                               width - margin, height - 2*margin)
        block.tab_count = self.tab_count
        block.draw_nicked_line(painter,
                               nick_radius,
                               margin, height - 2*margin,
                               (width - grid_width)/2, height - 2*margin)
        block.draw_nicked_line(painter,
                               nick_radius,
                               (width + grid_width)/2, height - 2*margin,
                               width - margin, height - 2*margin)

    def draw_cuts2(self,
                   painter: QPainter | LineDeduper,
                   nick_radius: int = 0):
        column_count = self.puzzles[0].grid.width
        grid_width = column_count * self.square_size
        width = painter.window().width()
        height = painter.window().height()
        margin = round(height / 66)  # Covers cutter drift

        block = Block(Square(' '))
        block.squares[0].size = self.square_size
        block.draw_nicked_line(painter,
                               nick_radius,
                               margin, 2*margin,
                               margin, height - margin)
        block.draw_nicked_line(painter,
                               nick_radius,
                               margin, height - margin,
                               width - margin, height - margin)
        block.draw_nicked_line(painter,
                               nick_radius,
                               width - margin, 2*margin,
                               width - margin, height - margin)
        block.tab_count = self.tab_count
        block.draw_nicked_line(painter,
                               nick_radius,
                               margin, 2*margin,
                               (width - grid_width)/2, 2*margin)
        block.draw_nicked_line(painter,
                               nick_radius,
                               (width + grid_width)/2, 2*margin,
                               width - margin, 2*margin)
