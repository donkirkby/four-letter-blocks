import math

from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter

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
                 block_packer: BlockPacker | None = None):
        super().__init__(front_puzzle, back_puzzle, block_packer)
        self.slug_index = 0

    def draw_header(self,
                    painter: QPainter,
                    puzzle: Puzzle,
                    font_size: float | None = None,
                    is_dry_run: bool = False) -> QRectF:
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

        clues_rect = QRectF(2*margin, clues_start, clues_width, clues_height)
        CluePainter.draw_text(clues_rect, 'Across', painter, is_bold=True)
        clue_painter = CluePainter(puzzle, font_size=font_size)
        clue_count = clue_painter.draw_clues(painter,
                                             puzzle.across_clues,
                                             clues_rect)

        clues_rect = QRectF(2*margin + clues_width + margin, clues_start,
                            clues_width, clues_height)
        clue_count += clue_painter.draw_clues(painter,
                                              puzzle.across_clues[clue_count:],
                                              clues_rect)
        clues_rect = QRectF(2*margin + 2*(clues_width + margin), clues_start,
                            clues_width, clues_height)
        clue_count += clue_painter.draw_clues(painter,
                                              puzzle.across_clues[clue_count:],
                                              clues_rect)
        clues_rect = QRectF(2*margin + 3*(clues_width + margin), clues_start,
                            clues_width, clues_height)
        clue_count += clue_painter.draw_clues(painter,
                                              puzzle.across_clues[clue_count:],
                                              clues_rect)
        return grid_rect

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
        return y < limit

    def draw_cuts(self,
                  painter: QPainter | LineDeduper,
                  nick_radius: int = 0,
                  header_fraction: float = 0.1):
        super().draw_cuts(painter, nick_radius, header_fraction)
        width = painter.window().width()
        height = painter.window().height()
        margin = round(height / 66)  # Covers cutter drift
        column_count = self.puzzles[0].grid.width
        grid_width = column_count * self.square_size

        painter.setPen(Block.CUT_COLOUR)

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
