from io import StringIO
from pathlib import Path
from textwrap import dedent

from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter, QColor, QImage, QFont, Qt

from four_letter_blocks.block import Block
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.clue_painter import CluePainter
from four_letter_blocks.puzzle import Puzzle, draw_rotated_tiles
from four_letter_blocks.puzzle_pair import PuzzlePair
from four_letter_blocks.square import draw_gradient_rect, Square
from tests.pixmap_differ import PixmapDiffer


def parse_puzzle_pair(block_packer: BlockPacker = None):
    puzzle1 = Puzzle.parse(StringIO(dedent("""\
        Front (5x5)

        #BUS#
        PEPPY
        ES#LE
        IOTAS
        #TOT#

        BESOT - Make drunk
        BUS - Bus clue erroneously beyond everyday page's voluminous boundary
        ES - es clue pleasantly truthful surrounding verdant foliage abundantly
        IOTAS - iotas clue with marginally transferrable containers wanderlust
        LE - francophone's direct article without extension or divergent structured landing
        PEI - pei clue leaves fragrant residue throughout residential thoroughfares
        PEPPY - Peppy clue makes foreign entangling continue
        SPLAT - splat clue extends through ridiculous depths
        TO - pointing out your destination within a wide range
        TOT - tot dot screams among flowering shrubbery lacks any fraught experience
        UP - up clue
        YES - supremely positive

        #DDD#
        AADCC
        AA#CC
        EEBBB
        #EEB#
    """)))
    puzzle2 = Puzzle.parse(StringIO(dedent("""\
        Back (5x5)

        #BAA#
        RINGO
        AC#NU
        METER
        #PIS#

        AC - 60 Hz
        AGNES - agnes clue
        AN - an clue
        BAA - baa clue
        BICEP - bicep clue
        METER - meter clue
        NU - nu clue
        OUR - our clue
        PIS - pis clue
        RAM - ram clue
        RINGO - ringo clue
        TI - ti clue

        #CCB#
        DCCBB
        DD#EB
        DAAEE
        #AAE#
    """)))
    pair = PuzzlePair(puzzle1, puzzle2, block_packer=block_packer)
    puzzle1.face_colour = QColor('transparent')
    puzzle2.face_colour = QColor('transparent')
    return pair


def test_draw_blocks(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(360, 180) as (actual, expected):
        expected.fillRect(0, 0, 360, 180, 'cornsilk')
        actual.fillRect(0, 0, 360, 180, 'cornsilk')
        puzzle_pair1 = parse_puzzle_pair()
        front, back = puzzle_pair1.puzzles

        assert front.shape_counts == back.flipped_shape_counts

        black = QColor('black')
        draw_gradient_rect(expected, black, 51.25, 31.25, 17.5, 17.5, 6.25)
        draw_gradient_rect(expected, black, 91.25, 31.25, 17.5, 17.5, 6.25)
        draw_gradient_rect(expected, black, 91.25, 51.25, 17.5, 17.5, 6.25)
        draw_gradient_rect(expected, black, 11.25, 51.25, 17.5, 17.5, 6.25)
        draw_gradient_rect(expected, black, 11.25, 91.25, 17.5, 17.5, 6.25)
        draw_gradient_rect(expected, black, 211.25, 91.25, 17.5, 17.5, 6.25)
        draw_gradient_rect(expected, black, 211.25, 51.25, 17.5, 17.5, 6.25)
        draw_gradient_rect(expected, black, 131.25, 51.25, 17.5, 17.5, 6.25)
        draw_gradient_rect(expected, black, 131.25, 31.25, 17.5, 17.5, 6.25)
        draw_gradient_rect(expected, black, 171.25, 31.25, 17.5, 17.5, 6.25)
        front.face_colour = QColor('transparent')
        back.face_colour = QColor('transparent')
        puzzle_pair1.square_size = 20
        blocks = front.blocks
        blocks[0].set_display(70, 70, 0)
        blocks[1].set_display(30, 50, 0)
        blocks[2].set_display(10, 10, 0)
        blocks[3].set_display(50, 10, 0)
        blocks[4].set_display(10, 70, 0)

        blocks = back.blocks
        blocks[0].set_display(130, 70, 0)
        blocks[1].set_display(170, 70, 0)
        blocks[2].set_display(190, 10, 0)
        blocks[3].set_display(150, 50, 0)
        blocks[4].set_display(130, 10, 0)

        for block in front.blocks + back.blocks:
            block.draw(expected, is_packed=True)

        puzzle_set2 = parse_puzzle_pair(BlockPacker(5, 5, tries=1000))
        puzzle_set2.square_size = 20
        puzzle_set2.draw_front_blocks(actual)

        actual.setViewport(120, 0, 360, 180)
        puzzle_set2.draw_back_blocks(actual)


def test_draw_header(pixmap_differ: PixmapDiffer):
    with pixmap_differ.create_painters(500, 260):
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter
        grid_rect = QRectF(170, 9.09, 160, 160)

        pair = parse_puzzle_pair()
        pair.square_size = 32
        front_puzzle, back_puzzle = pair.puzzles

        font = expected.font()
        font.setPixelSize(12)
        expected.setFont(font)
        CluePainter.draw_text(grid_rect,
                              front_puzzle.title,
                              expected,
                              is_centred=True)

        font.setPixelSize(8)
        expected.setFont(font)
        CluePainter.draw_text(grid_rect, front_puzzle.build_hints(), expected)
        font.setPixelSize(4)
        expected.setFont(font)
        CluePainter.draw_text(grid_rect,
                              pair.LINK_TEXT,
                              expected,
                              is_centred=True)
        grid_rect.translate(0, 9.09)
        grid_rect.setHeight(160)

        expected.fillRect(grid_rect, 'grey')

        actual_grid_rect = pair.draw_header(actual, front_puzzle, font_size=8)
        actual.fillRect(actual_grid_rect, 'grey')


def test_draw_clues(pixmap_differ: PixmapDiffer):
    with pixmap_differ.create_painters(500, 260):
        pixmap_differ.radius = 2
        pixmap_differ.tolerance = 25
        actual = pixmap_differ.actual.painter
        expected = pixmap_differ.expected.painter

        pair1 = parse_puzzle_pair()
        pair1.square_size = 32
        front_puzzle, back_puzzle = pair1.puzzles
        font = QFont('NotoSansCJK')
        expected.setFont(font)

        grid_rect = pair1.draw_header(expected, front_puzzle, font_size=8)

        font.setPixelSize(8)
        expected.setFont(font)

        expected.fillRect(grid_rect, 'grey')

        number_width = CluePainter.find_text_width('10.', expected)
        padded_width = CluePainter.find_text_width('10. ', expected)
        font.setBold(True)
        expected.setFont(font)
        margin = 9
        clues_rect = QRectF(margin, margin, 150, 260)
        CluePainter.draw_text(clues_rect, 'Across', expected)
        font.setBold(False)
        expected.setFont(font)
        num_rect = QRectF(clues_rect)
        num_rect.setWidth(number_width)
        clues_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(num_rect,
                              '1.\n\n2.\n\n\n5.\n\n\n6.\n\n\n9.\n\n\n10.',
                              expected,
                              is_aligned_right=True)
        across_text = dedent("""\
            Peppy clue makes foreign entangling continue
            es clue pleasantly truthful surrounding verdant foliage abundantly
            francophone's direct article without extension or divergent structured landing
            Bus clue erroneously beyond everyday page's voluminous boundary
            iotas clue with marginally transferrable containers wanderlust
            tot dot screams among flowering shrubbery lacks any fraught experience""")
        CluePainter.draw_text(clues_rect, across_text, expected)

        number_width = CluePainter.find_text_width('8.', expected)
        padded_width = number_width + CluePainter.find_text_width(' ', expected)
        font.setBold(True)
        expected.setFont(font)
        clues_rect.setLeft(num_rect.left())
        CluePainter.draw_text(clues_rect, 'Down', expected)
        font.setBold(False)
        expected.setFont(font)
        num_rect = QRectF(clues_rect)
        num_rect.setWidth(number_width)
        clues_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(num_rect,
                              '1.\n\n\n3.',
                              expected,
                              is_aligned_right=True)
        across_text = dedent("""\
            pei clue leaves fragrant residue
            throughout residential
            thoroughfares
            pointing out your destination within a wide range""")
        CluePainter.draw_text(clues_rect, across_text, expected)

        clues_rect = QRectF(grid_rect)
        clues_rect.moveTop(clues_rect.bottom() + margin)
        clues_rect.setRight((clues_rect.left() + clues_rect.right())/2)
        num_rect = QRectF(clues_rect)
        num_rect.setWidth(number_width)
        clues_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(num_rect,
                              '4.',
                              expected,
                              is_aligned_right=True)
        CluePainter.draw_text(clues_rect,
                              'supremely positive',
                              expected)

        clues_rect = QRectF(grid_rect.left() + (grid_rect.width() + margin)//2,
                            grid_rect.bottom() + margin,
                            (grid_rect.width() - margin) // 2,
                            1000)

        num_rect = QRectF(clues_rect)
        num_rect.setWidth(number_width)
        clues_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(num_rect,
                              '6.\n7.',
                              expected,
                              is_aligned_right=True)
        CluePainter.draw_text(clues_rect,
                              'Make drunk\nup clue',
                              expected)

        clues_rect = QRectF(grid_rect.right() + margin, margin,
                            1000, 1000)

        num_rect = QRectF(clues_rect)
        num_rect.setWidth(number_width)
        clues_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(num_rect,
                              '8.',
                              expected,
                              is_aligned_right=True)
        CluePainter.draw_text(clues_rect,
                              'splat clue extends through\nridiculous depths',
                              expected)

        actual.setFont(QFont('NotoSansCJK'))
        pair2 = parse_puzzle_pair()
        front_puzzle, back_puzzle = pair2.puzzles
        front_puzzle.square_size = 32
        actual_grid_rect = pair2.draw_header(actual, front_puzzle, font_size=8)
        actual.fillRect(actual_grid_rect, 'grey')

        pair2.draw_clues(actual, grid_rect, front_puzzle, font_size=8)


def test_draw_front(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(500, 260) as (actual, expected):
        expected.fillRect(0, 0, 500, 300, 'cornsilk')
        actual.fillRect(0, 0, 500, 300, 'cornsilk')
        pair1 = parse_puzzle_pair()
        pair1.square_size = 30
        front_puzzle, back_puzzle = pair1.puzzles
        grid_rect = pair1.draw_header(expected, front_puzzle, font_size=9)
        pair1.draw_clues(expected, grid_rect, front_puzzle, font_size=9)
        expected.translate(grid_rect.left() - pair1.square_size/2,
                           grid_rect.top() - pair1.square_size/2)
        pair1.draw_front_blocks(expected)

        pair2 = parse_puzzle_pair()
        pair2.square_size = 30
        pair2.draw_front(actual, font_size=9)


def test_draw_cuts(pixmap_differ: PixmapDiffer):
    block_text = dedent("""\
        AABBB
        AA#B#
        #CCC#
        DDCEE
        #DDEE
    """)
    puzzle = Puzzle.parse_sections('',
                                   block_text,
                                   '',
                                   block_text)
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(500, 260) as (actual, expected):
        expected.fillRect(0, 0, 500, 300, 'cornsilk')
        actual.fillRect(0, 0, 500, 300, 'cornsilk')
        puzzle.square_size = 30

        pen = expected.pen()
        pen.setColor(Block.CUT_COLOUR)
        pen.setCapStyle(Qt.PenCapStyle.FlatCap)
        expected.setPen(pen)
        expected.drawLine(4, 4, 496, 4)
        expected.drawLine(4, 4, 4, 256)
        expected.drawLine(4, 256, 496, 256)
        expected.drawLine(496, 4, 496, 256)
        expected.translate(175, 26)
        for block in puzzle.blocks:
            block.tab_count = 2
            block.border_colour = block.CUT_COLOUR
            block.draw_outline(expected)
        block = Block(Square(' '))
        block.squares[0].size = puzzle.square_size
        block.tab_count = 2
        block.border_colour = block.CUT_COLOUR
        for block.x, block.y in ((120, 30), (0, 60), (120, 60), (0, 120)):
            block.draw_outline(expected)

        pair2 = parse_puzzle_pair()
        pair2.square_size = 30
        pair2.tab_count = 2
        pair2.draw_cuts(actual, header_fraction=0.1)


def test_draw_back(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(500, 260) as (actual, expected):
        pair1 = parse_puzzle_pair()
        pair1.square_size = 30
        front_puzzle, back_puzzle = pair1.puzzles
        grid_rect = pair1.draw_header(expected, back_puzzle, font_size=10)
        pair1.draw_clues(expected, grid_rect, back_puzzle, font_size=10)
        expected.translate(grid_rect.left() - pair1.square_size/2,
                           grid_rect.top() - pair1.square_size/2)
        pair1.draw_back_blocks(expected)

        pair2 = parse_puzzle_pair()
        pair2.square_size = 30
        pair2.draw_back(actual, font_size=10)


def test_packing(pixmap_differ: PixmapDiffer):
    expected_packing = dedent("""\
        AABBB
        AA#B#
        #CCC#
        DDCEE
        .DDEE""")
    puzzle_pair = parse_puzzle_pair(BlockPacker(5, 5, tries=1000))

    packing = puzzle_pair.block_packer.display()

    assert packing == expected_packing


def test_prepacking(pixmap_differ: PixmapDiffer):
    expected_packing = dedent("""\
        #CCC#
        DDCEE
        .DDEE
        AABBB
        AA#B#""")
    puzzle_pair = parse_puzzle_pair(BlockPacker(start_text=expected_packing,
                                                tries=1000))

    packing = puzzle_pair.block_packer.display()

    assert packing == expected_packing


def test_prepacking_flipped(pixmap_differ: PixmapDiffer):
    start_text = dedent("""\
        #CCC#
        EECDD
        EEDD.
        BBBAA
        #B#AA""")
    expected_packing = dedent("""\
        #CCC#
        DDCEE
        .DDEE
        AABBB
        AA#B#""")
    puzzle_pair = parse_puzzle_pair(BlockPacker(start_text=start_text,
                                                tries=1000))

    packing = puzzle_pair.block_packer.display()

    assert packing == expected_packing


def test_prepacking_useless(pixmap_differ: PixmapDiffer):
    start_text = dedent("""\
        AAAA
        BBBB
        CCCC
        DDDD""")
    expected_packing = dedent("""\
        AABBB
        AA#B#
        #CCC#
        DDCEE
        .DDEE""")
    puzzle_pair = parse_puzzle_pair(BlockPacker(start_text=start_text,
                                                tries=1000))

    packing = puzzle_pair.block_packer.display()

    assert packing == expected_packing


# noinspection DuplicatedCode
def test_background_tile(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(500, 260) as (actual, expected):
        expected_image = QImage(Path(__file__).parent / 'pair_tile.png')
        expected.drawImage(0, 0, expected_image)

        actual.setBackground(QColor('burlywood'))
        actual.eraseRect(actual.window())

        actual.setWindow(0, 0, 260, 260)
        actual.setViewport(actual.window().translated(120, 0))
        puzzle_pair = parse_puzzle_pair()
        puzzle_pair.draw_background_tile(actual)


def test_background_pattern(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(520, 260) as (actual, expected):
        expected_image = QImage(Path(__file__).parent / 'pair_pattern.png')
        expected.drawImage(0, 0, expected_image)

        actual.setBackground(QColor('burlywood'))

        puzzle_pair = parse_puzzle_pair()
        puzzle_pair.draw_background_pattern(actual, size=260 // 6)


def test_background_pattern_offset(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(520, 260) as (actual, expected):
        expected_image = QImage(Path(__file__).parent /
                                'pair_pattern_offset.png')
        expected.drawImage(0, 0, expected_image)

        actual.setBackground(QColor('burlywood'))

        size = 260 / 6
        puzzle_pair = parse_puzzle_pair()
        puzzle_pair.draw_background_pattern(actual,
                                            size,
                                            x_offset=int(size*1.5),
                                            y_offset=int(size*1.333))


def test_background_pattern_bounds(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(520, 260) as (actual, expected):
        expected_image = QImage(Path(__file__).parent /
                                'pair_pattern_offset.png')
        expected.fillRect(expected.window(), 'burlywood')
        expected.drawImage(100, 100,
                           expected_image,
                           0, 0,
                           100, 100)

        actual.setBackground(QColor('burlywood'))
        actual.eraseRect(actual.window())

        puzzle_pair = parse_puzzle_pair()
        size = 260 / 6
        tile = puzzle_pair.create_background_tile(round(size),
                                                  QColor('burlywood'))
        draw_rotated_tiles(tile,
                           actual,
                           size,
                           x_offset=int(size*1.5),
                           y_offset=int(size*1.33),
                           bounds=QRectF(100, 100, 100, 100))
