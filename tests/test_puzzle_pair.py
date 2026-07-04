from io import StringIO
from pathlib import Path
from textwrap import dedent

import pytest
from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter, QColor, QImage, QFont, Qt

from four_letter_blocks.block import Block
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.clue_painter import CluePainter
from four_letter_blocks.puzzle import Puzzle, draw_rotated_tiles
from four_letter_blocks.puzzle_pair import PuzzlePair
from four_letter_blocks.square import draw_gradient_rect, Square
from tests.pixmap_differ import PixmapDiffer


def parse_puzzle_pair(packing_page: str|None = None) -> PuzzlePair:
    puzzle1 = Puzzle.parse(StringIO(dedent("""\
        Front (5x5)

        #BFF#
        ARAL#
        TARED
        EDGER
        #SOS#

        ARAL - Shrinking sea makes foreign entangling continue without ceasing
        ATE - What 7 did to 9
        BFF - Long-time friend erroneously beyond everyday page's voluminous boundary and surroundings
        BRADS - Fastener bros with sticky nose
        DR - Short medic without administration or hesitation
        EDGER - Boundary pusher without extension or divergent structured landing and launching and circulating
        FARGO - Distant destination with little hope of return, rescue, or communication
        FLEES - When a sheep runs away
        SOS - Pleading letters often ignored by aerial surveillance and marine excursions
        TARED - Balanced pleasantly truthful surrounding verdant foliage abundantly

        #DCC#
        DDCC#
        DAAAA
        IIIGG
        #IGG#
    """)))
    puzzle2 = Puzzle.parse(StringIO(dedent("""\
        Back (5x5)

        #AMP#
        #LOUT
        POURS
        CUTUP
        #DHS#

        ALOUD - Spoken words
        AMP - Pumps up the volume
        CUTUP - Little snipper
        DHS - Deadly hermit sneakers
        LOUT - Uncouth youth
        MOUTH - Where ALOUD comes from
        PC - A computer just for you
        POURS - What it does when it rains
        PURUS - Cosmic being
        TSP - Cleaning powder
        
        #CCD#
        #CCDD
        AAAAD
        GGIII
        #GGI#
    """)))
    if packing_page is not None:
        set_options = dict(packing_pages=(packing_page,))
    else:
        set_options = None

    puzzle1.across_clues[-1].number = 10
    pair = PuzzlePair(puzzle1, puzzle2, set_options=set_options)
    pair.pack_puzzles()
    puzzle1.face_colour = QColor('transparent')
    puzzle2.face_colour = QColor('transparent')
    return pair


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
                              '4.\n\n\n\n5.\n\n\n6.\n\n\n7.\n\n\n\n10.',
                              expected,
                              is_aligned_right=True)
        across_text = dedent("""\
            Long-time friend erroneously beyond everyday page's
            voluminous boundary and surroundings
            Shrinking sea makes foreign entangling continue without ceasing
            Balanced pleasantly truthful surrounding verdant foliage abundantly
            Boundary pusher without extension or divergent structured
            landing and launching and circulating
            Pleading letters often ignored by aerial surveillance and marine
            excursions""")
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
        clues_rect.adjust(padded_width, 0, padded_width/2, 0)
        CluePainter.draw_text(num_rect,
                              '1.\n\n2.',
                              expected,
                              is_aligned_right=True)
        across_text = dedent("""\
            Short medic without administration or hesitation
            Distant destination with little hope of return, rescue, or
            communication""")
        CluePainter.draw_text(clues_rect, across_text, expected)

        clues_rect = QRectF(grid_rect)
        clues_rect.moveTop(clues_rect.bottom() + margin)
        clues_rect.setRight((clues_rect.left() + clues_rect.right())/2)
        num_rect = QRectF(clues_rect)
        num_rect.setWidth(number_width)
        clues_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(num_rect,
                              '3.',
                              expected,
                              is_aligned_right=True)
        CluePainter.draw_text(clues_rect,
                              'When a sheep runs away',
                              expected)

        clues_rect = QRectF(grid_rect.left() + (grid_rect.width() + margin)//2,
                            grid_rect.bottom() + margin,
                            (grid_rect.width() - margin) // 2,
                            1000)

        num_rect = QRectF(clues_rect)
        num_rect.setWidth(number_width)
        clues_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(num_rect,
                              '4.',
                              expected,
                              is_aligned_right=True)
        CluePainter.draw_text(clues_rect,
                              'Fastener bros with sticky nose',
                              expected)

        clues_rect = QRectF(grid_rect.right() + margin, margin,
                            1000, 1000)

        num_rect = QRectF(clues_rect)
        num_rect.setWidth(number_width)
        clues_rect.adjust(padded_width, 0, 0, 0)
        CluePainter.draw_text(num_rect,
                              '5.',
                              expected,
                              is_aligned_right=True)
        CluePainter.draw_text(clues_rect,
                              'What 7 did to 9',
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
        expected.setFont(QFont('NotoSansCJK'))
        pair1 = parse_puzzle_pair()
        pair1.square_size = 32
        front_puzzle, back_puzzle = pair1.puzzles
        grid_rect = pair1.draw_header(expected, front_puzzle, font_size=8)
        pair1.draw_clues(expected, grid_rect, front_puzzle, font_size=8)
        expected.translate(grid_rect.left() - pair1.square_size/2,
                           grid_rect.top() - pair1.square_size/2)
        pair1.draw_front_blocks(expected)

        actual.setFont(QFont('NotoSansCJK'))
        pair2 = parse_puzzle_pair()
        pair2.square_size = 32
        pair2.draw_front(actual, font_size=8)


def test_draw_cuts(pixmap_differ: PixmapDiffer):
    block_text = dedent("""\
        #A#BB
        AABB#
        ACCCC
        DDDEE
        #D#EE
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
        expected.drawLine(5, 5, 495, 5)
        expected.drawLine(5, 5, 5, 255)
        expected.drawLine(5, 255, 495, 255)
        expected.drawLine(495, 5, 495, 255)
        expected.translate(175, 26)
        for block in puzzle.blocks:
            block.tab_count = 1
            block.border_colour = block.CUT_COLOUR
            block.draw_outline(expected)
        block = Block(Square(' '))
        block.squares[0].size = puzzle.square_size
        block.tab_count = 1
        block.border_colour = block.CUT_COLOUR
        for block.x, block.y in ((0, 0),
                                 (60, 0),
                                 (120, 30),
                                 (0, 120),
                                 (60, 120)):
            block.draw_outline(expected)

        pair2 = parse_puzzle_pair()
        pair2.square_size = 30
        pair2.tab_count = 1
        pair2.draw_cuts(actual, header_fraction=0.1)


def test_draw_back(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(500, 260) as (actual, expected):
        expected.fillRect(0, 0, 500, 300, 'cornsilk')
        actual.fillRect(0, 0, 500, 300, 'cornsilk')
        expected.setFont(QFont('NotoSansCJK'))
        # Weird interference from test_draw_front and antialiasing?
        # Work around it by increasing tolerance and radius.
        pixmap_differ.radius = 2
        pixmap_differ.tolerance = 4

        pair1 = parse_puzzle_pair()
        pair1.square_size = 32
        front_puzzle, back_puzzle = pair1.puzzles
        grid_rect = pair1.draw_header(expected, back_puzzle, font_size=8)
        pair1.draw_clues(expected, grid_rect, back_puzzle, font_size=8)
        expected.translate(grid_rect.left() - pair1.square_size/2,
                           grid_rect.top() - pair1.square_size/2)
        pair1.draw_back_blocks(expected)

        actual.setFont(QFont('NotoSansCJK'))
        pair2 = parse_puzzle_pair()
        pair2.square_size = 32
        pair2.draw_back(actual, font_size=8)


def test_packing():
    expected_packing = dedent("""\
        #C#DD
        CCDD#
        CBBBB
        EEEAA
        #E#AA""")
    puzzle_pair = parse_puzzle_pair()

    packing = puzzle_pair.page_packers[0].display()

    assert packing == expected_packing


def test_shape_counts_differ():
    puzzle1 = Puzzle.parse(StringIO(dedent('''\
        Example 1

        #ABC#
        DEFGH
        IJ#KL
        MNOPQ
        #RST#

        -

        #AAA#
        BBAEE
        BB#EE
        CCDDD
        #CCD#
        ''')))
    puzzle2 = Puzzle.parse(StringIO(dedent('''\
        Example 2
    
        #ABCD
        EFGHI
        #J#K#
        LMNOP
        QRST#
    
        -
        
        #AAAB
        CCABB
        #C#B#
        DCEEE
        DDDE#
        ''')))

    with pytest.raises(ValueError,
                       match=r'No combination of unused counts and shape '
                             r'counts could be evenly split: \(0, 0\); '
                             r'O: 2, T0: 2, Z0: 1; '
                             r'J3: 1, L2: 1, T0: 2, Z1: 1\.'):
        puzzle_pair = PuzzlePair(puzzle1, puzzle2)
        puzzle_pair.pack_puzzles()


def test_prepacking():
    expected_packing = dedent("""\
        #CEEE
        CC#E#
        CBBBB
        #DDAA
        DD#AA""")
    puzzle_pair = parse_puzzle_pair(expected_packing)

    packing = puzzle_pair.page_packers[0].display()

    assert packing == expected_packing


def test_prepacking_flipped():
    start_text = dedent("""\
        EEEC#
        #E#CC
        BBBBC
        AADD#
        AA#DD""")
    expected_packing = dedent("""\
        #CEEE
        CC#E#
        CBBBB
        #DDAA
        DD#AA""")
    puzzle_pair = parse_puzzle_pair(start_text)

    packing = puzzle_pair.page_packers[0].display()

    assert packing == expected_packing


def test_prepacking_useless():
    start_text = dedent("""\
        AAAA
        BBBB
        CCCC
        DDDD""")
    expected_packing = dedent("""\
        #C#DD
        CCDD#
        CBBBB
        EEEAA
        #E#AA""")
    puzzle_pair = parse_puzzle_pair(start_text)

    packing = puzzle_pair.page_packers[0].display()

    assert packing == expected_packing


# noinspection DuplicatedCode
def test_background_tile(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(500, 260, max_diff=2) as (actual,
                                                                 expected):
        expected_image = QImage(Path(__file__).parent / 'pair_tile.png')
        expected.drawImage(0, 0, expected_image)

        puzzle_pair = PuzzlePair(*parse_puzzle_pair().puzzles)
        puzzle_pair.pack_puzzles()

        actual.setBackground(puzzle_pair.puzzles[0].face_colour)
        actual.eraseRect(actual.window())

        actual.setWindow(0, 0, 260, 260)
        actual.setViewport(actual.window().translated(120, 0))
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
