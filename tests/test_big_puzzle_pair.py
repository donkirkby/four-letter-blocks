from pathlib import Path

from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter, QColor

from four_letter_blocks.big_puzzle_pair import BigPuzzlePair
from four_letter_blocks.block import Block
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.clue_painter import CluePainter
from four_letter_blocks.puzzle import Puzzle
from four_letter_blocks.square import Square
from tests.pixmap_differ import PixmapDiffer


# noinspection DuplicatedCode
def test_draw_front_slug1(pixmap_differ: PixmapDiffer):
    front_file = Path(__file__).parent / 'test-front11x11.txt'
    back_file = Path(__file__).parent / 'test-back11x11.txt'
    with front_file.open() as f:
        front_puzzle = Puzzle.parse(f)
    with back_file.open() as f:
        back_puzzle = Puzzle.parse(f)
    packer = BlockPacker(width=11, height=11, split_row=5, tries=100)
    pair = BigPuzzlePair(front_puzzle, back_puzzle, packer)
    pair.margin = 10
    front_puzzle.square_size = 25
    width = 333
    height = round(width / 10.5 * 8.25)
    expected: QPainter
    actual: QPainter
    with pixmap_differ.create_painters(width, height) as (actual, expected):
        font = expected.font()
        font.setPixelSize(12)
        expected.setFont(font)
        title_rect = QRectF(8, 8, 325, height-8)
        title_width = CluePainter.find_text_width(front_puzzle.title, expected)
        intro_rect = title_rect.adjusted(title_width+4, 0, 0, 0)
        CluePainter.draw_text(title_rect, front_puzzle.title, expected)
        font.setPixelSize(8)
        expected.setFont(font)
        CluePainter.draw_text(intro_rect,
                              front_puzzle.build_hints(),
                              expected)
        header_height = max(title_rect.top(), intro_rect.top()) + 4
        clue_width = 317 / 4 - 4
        clue_height = height - header_height - 141
        clue_rect = QRectF(8, header_height, clue_width, clue_height)
        CluePainter.draw_text(clue_rect, 'Across', expected, is_bold=True)
        clue_painter = CluePainter(front_puzzle)
        clue_count = clue_painter.draw_clues(expected,
                                             front_puzzle.across_clues,
                                             clue_rect)
        clue_rect = QRectF(8+clue_width+4, header_height,
                           clue_width, clue_height)
        clue_count += clue_painter.draw_clues(
            expected,
            front_puzzle.across_clues[clue_count:],
            clue_rect)
        clue_rect = QRectF(8+2*(clue_width+4), header_height,
                           clue_width, clue_height)
        clue_count += clue_painter.draw_clues(
            expected,
            front_puzzle.across_clues[clue_count:],
            clue_rect)
        clue_rect = QRectF(20+3*clue_width, header_height,
                           clue_width, clue_height)
        clue_painter.draw_clues(
            expected,
            front_puzzle.across_clues[clue_count:],
            clue_rect)
        bottom = height - 8
        x_shift = (333 - 12 * pair.square_size) / 2
        y_shift = height - 145.5
        expected.translate(x_shift, y_shift)
        for block in pair.display_blocks(pair.block_packer, pair.front_blocks):
            if block.display_y < 125:
                block.draw(expected, is_packed=True)
        black_block = Block(Square(' '))
        black_block.squares[0].size = pair.square_size
        black_block.face_colour = QColor('black')
        black_block.border_colour = Block.CUT_COLOUR
        black_block.tab_count = 2
        black_positions = ((37.5, 37.5),
                           (112.5, 37.5),
                           (187.5, 37.5),
                           (262.5, 62.5),
                           (12.5, 87.5),
                           (162.5, 87.5),
                           (87.5, 112.5))
        for black_block.x, black_block.y in black_positions:
            black_block.draw(expected, is_packed=True)

        # cuts
        pen = expected.pen()
        pen.setColor(Block.CUT_COLOUR)
        expected.setPen(pen)
        expected.translate(-x_shift, -y_shift)
        expected.drawLine(4, 4, 329, 4)
        expected.drawLine(4, 4, 4, bottom)
        expected.drawLine(329, 4, 329, bottom)
        black_block.draw_nicked_line(expected,
                                     0,
                                     4, bottom,
                                     round(x_shift + 12.5), bottom)
        black_block.draw_nicked_line(expected,
                                     0,
                                     round(x_shift + 287.5), bottom,
                                     329, bottom)

        expected.translate(x_shift, y_shift)
        for block in pair.display_blocks(pair.block_packer, pair.front_blocks):
            if block.display_y < 125:
                block.tab_count = 2
                block.border_colour = Block.CUT_COLOUR
                block.draw_outline(expected)
        for black_block.x, black_block.y in black_positions:
            black_block.draw_outline(expected)

        pair.tab_count = 2
        grid_rect = pair.draw_front(actual, font_size=8)
        header_fraction = grid_rect.top() / height
        pair.draw_cuts(actual, header_fraction=header_fraction)


# noinspection DuplicatedCode
def test_draw_front_slug2(pixmap_differ: PixmapDiffer):
    front_file = Path(__file__).parent / 'test-front11x11.txt'
    back_file = Path(__file__).parent / 'test-back11x11.txt'
    with front_file.open() as f:
        front_puzzle = Puzzle.parse(f)
    with back_file.open() as f:
        back_puzzle = Puzzle.parse(f)
    packer = BlockPacker(width=11, height=11, split_row=5, tries=100)
    pair = BigPuzzlePair(front_puzzle, back_puzzle, packer)
    pair.margin = 10
    front_puzzle.square_size = 25
    width = 333
    height = round(width / 10.5 * 8.25)
    expected: QPainter
    actual: QPainter
    with pixmap_differ.create_painters(width, height) as (actual, expected):
        font = expected.font()
        font.setPixelSize(4)
        expected.setFont(font)
        expected.rotate(-90)
        frame_start = width - (width - 275) / 2
        link_height = CluePainter.find_text_height(pair.LINK_TEXT, expected)
        link_start = (width + frame_start - 4 - link_height) / 2
        link_rect = QRectF(-158, link_start, 150, width)
        CluePainter.draw_text(link_rect,
                              pair.LINK_TEXT,
                              expected,
                              is_centred=True)
        expected.rotate(90)
        font.setPixelSize(8)
        expected.setFont(font)
        clue_width = 317 / 4 - 4
        clue_height = height - 174
        clue_rect = QRectF(8, 166, clue_width, clue_height)
        CluePainter.draw_text(clue_rect, 'Down', expected, is_bold=True)
        clue_painter = CluePainter(front_puzzle)
        clue_count = clue_painter.draw_clues(expected,
                                             front_puzzle.down_clues,
                                             clue_rect)
        clue_rect = QRectF(8+clue_width+4, 166, clue_width, clue_height)
        clue_count += clue_painter.draw_clues(
            expected,
            front_puzzle.down_clues[clue_count:],
            clue_rect)
        clue_rect = QRectF(8+2*(clue_width+4), 166, clue_width, clue_height)
        clue_count += clue_painter.draw_clues(
            expected,
            front_puzzle.down_clues[clue_count:],
            clue_rect)
        clue_rect = QRectF(8+3*(clue_width+4), 166, clue_width, clue_height)
        clue_painter.draw_clues(
            expected,
            front_puzzle.down_clues[clue_count:],
            clue_rect)

        x_shift = (333 - 12 * pair.square_size) / 2
        y_shift = -129.5
        expected.translate(x_shift, y_shift)
        for block in pair.display_blocks(pair.block_packer, pair.front_blocks):
            if block.display_y > 125:
                block.draw(expected, is_packed=True)

        black_block = Block(Square(' '))
        black_block.squares[0].size = pair.square_size
        black_block.face_colour = QColor('black')
        black_block.tab_count = 2
        black_positions = ((12.5, 162.5),
                           (187.5, 162.5),
                           (237.5, 162.5),
                           (237.5, 187.5),
                           (12.5, 212.5),
                           (62.5, 237.5),
                           (87.5, 237.5),
                           (137.5, 237.5),
                           (237.5, 237.5),
                           (262.5, 237.5),
                           (12.5, 262.5),
                           (87.5, 262.5),
                           (137.5, 262.5),
                           (162.5, 262.5),
                           (187.5, 262.5),
                           (212.5, 262.5),
                           (237.5, 262.5),
                           (262.5, 262.5))
        for black_block.x, black_block.y in black_positions:
            black_block.draw(expected, is_packed=True)

        # cuts
        expected.setPen(Block.CUT_COLOUR)
        expected.translate(-x_shift, -y_shift)
        expected.drawLine(4, height-4, 329, height-4)
        expected.drawLine(4, 8, 4, height-4)
        expected.drawLine(329, 8, 329, height-4)
        black_block.draw_nicked_line(expected,
                                     0,
                                     4, 8,
                                     round(x_shift+12.5), 8)
        black_block.draw_nicked_line(expected,
                                     0,
                                     round(x_shift+287.5), 8,
                                     329, 8)
        expected.translate(x_shift, y_shift)
        for block in pair.display_blocks(pair.block_packer, pair.front_blocks):
            block.border_colour = Block.CUT_COLOUR
            if block.display_y > 125:
                block.tab_count = 2
                block.draw_outline(expected)
        black_block.border_colour = Block.CUT_COLOUR
        for black_block.x, black_block.y in black_positions:
            black_block.draw_outline(expected)

        pair.tab_count = 2
        pair.slug_index = 1
        grid_rect = pair.draw_front(actual, font_size=8)
        header_fraction = grid_rect.top() / height
        pair.draw_cuts(actual, header_fraction=header_fraction)
