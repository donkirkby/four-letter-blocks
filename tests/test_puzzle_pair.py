from io import StringIO
from textwrap import dedent

from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter, QColor, Qt

from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.puzzle import Puzzle
from four_letter_blocks.puzzle_pair import PuzzlePair
from four_letter_blocks.square import draw_gradient_rect
from tests.pixmap_differ import PixmapDiffer


def parse_puzzle_pair(block_packer: BlockPacker = None):
    puzzle1 = Puzzle.parse(StringIO(dedent("""\
        Front

        #BUS#
        PEPPY
        ES#LE
        IOTAS
        #TOT#

        BESOT - Make drunk
        BUS - Bus clue that's too long to fit on the page
        ES - es clue peas clue must be true
        IOTAS - iotas clue
        LE - le cleu tres longue
        PEI - pei clue
        PEPPY - Peppy clue for two and you too
        SPLAT - splat clue
        TO - to clue
        TOT - tot dot
        UP - up clue
        YES - yes clue

        #DDD#
        AADCC
        AA#CC
        EEBBB
        #EEB#
    """)))
    puzzle2 = Puzzle.parse(StringIO(dedent("""\
        Back

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
    return PuzzlePair(puzzle1, puzzle2, block_packer=block_packer)


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


def test_draw_clues(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(500, 260) as (actual, expected):
        expected.fillRect(0, 0, 500, 300, 'cornsilk')
        actual.fillRect(0, 0, 500, 300, 'cornsilk')
        grid_rect = QRect(150, 45, 200, 200)
        expected.fillRect(grid_rect, 'grey')
        actual.fillRect(grid_rect, 'grey')

        expected.drawText(9, 23, 'Across')
        expected.drawText(QRect(9, 26, 21, 300),
                          int(Qt.AlignRight),
                          '1.\n\n\n2.\n\n\n5.\n\n6.\n\n\n9.')
        expected.drawText(QRect(33, 26, 100, 300),
                          dedent("""\
                            Peppy clue for
                            two and you
                            too
                            es clue peas
                            clue must be
                            true
                            le cleu tres
                            longue
                            Bus clue that's
                            too long to fit
                            on the page
                            iotas clue"""))
        expected.drawText(QRect(150, 9, 21, 300), int(Qt.AlignRight), '10.')
        expected.drawText(QRect(174, 9, 100, 300), 0, 'tot dot')

        expected.drawText(QRect(250, 9, 100, 300), 0, 'Down')
        expected.drawText(QRect(349, 9, 21, 300),
                          int(Qt.AlignRight),
                          '1.\n3.\n4.\n6.\n7.\n8.')
        expected.drawText(QRect(373, 9, 100, 300),
                          dedent("""\
                            pei clue
                            to clue
                            yes clue
                            Make drunk
                            up clue
                            splat clue"""))

        pair = parse_puzzle_pair()
        pair.square_size = 40
        front_puzzle, back_puzzle = pair.puzzles

        pair.draw_clues(actual, grid_rect, front_puzzle, font_size=15)


def test_draw_front(pixmap_differ: PixmapDiffer):
    actual: QPainter
    expected: QPainter
    with pixmap_differ.create_painters(500, 260) as (actual, expected):
        expected.fillRect(0, 0, 500, 300, 'cornsilk')
        actual.fillRect(0, 0, 500, 300, 'cornsilk')
        grid_rect = QRect(150, 45, 200, 200)
        pair1 = parse_puzzle_pair()
        front_puzzle, back_puzzle = pair1.puzzles
        pair1.square_size = 40
        pair1.draw_clues(expected, grid_rect, front_puzzle)
        expected.translate(130, 25)
        pair1.draw_front_blocks(expected)

        pair2 = parse_puzzle_pair()
        pair2.square_size = 40
        pair2.draw_front(actual)


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
