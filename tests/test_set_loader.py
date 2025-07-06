from pathlib import Path
from textwrap import dedent

from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.puzzle import Puzzle
from four_letter_blocks.puzzle_pair import PuzzlePair
from four_letter_blocks.puzzle_set import PuzzleSet
from four_letter_blocks.set_loader import read_puzzle_set, write_puzzle_set

PUZZLE_TEXT1 = dedent('''\
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
    ''')
"""
                AA.BB.
                AABBCC
                DDDECC
                .D.E..
                ..EEGG
                FFFGGH
                .FIIIH
                ...IHH
"""
PUZZLE_TEXT2 = dedent('''\
    Example 2

    #A#BC
    DEFGH
    IJ#KL
    MNOPQ
    RS#T#

    -

    #B#AA
    BBAAE
    CB#EE
    CDDDE
    CC#D#
    ''')

PUZZLE_TEXT3 = dedent('''\
    Example 3

    #ABCD
    EFGHI
    #J#K#
    LMNOP
    QRST#

    -

    #ABBB
    AAAFB
    #C#F#
    CCEFF
    CEEE#
    ''')

def test_read_set(tmp_path: Path) -> None:
    for file_name, puzzle_text in (('example1.txt', PUZZLE_TEXT1),
                                   ('example2.txt', PUZZLE_TEXT2),
                                   ('example3.txt', PUZZLE_TEXT3)):
        file_path = tmp_path / file_name
        file_path.write_text(puzzle_text)

    set_path = tmp_path / 'set.flb'
    set_path.write_text('''\
        type: PuzzleSet
        puzzles:
            - example2.txt
            - example3.txt
            - example1.txt
        start_hue: 30
        ''')

    puzzle_set = read_puzzle_set(set_path)

    assert isinstance(puzzle_set, PuzzleSet)
    assert len(puzzle_set.puzzles) == 3
    assert puzzle_set.puzzles[0].title == 'Example 2'
    assert puzzle_set.puzzles[2].title == 'Example 1'
    assert puzzle_set.start_hue == 30
    assert puzzle_set.block_packer.state.shape == (20, 16)

def test_read_pair(tmp_path: Path) -> None:
    for file_name, puzzle_text in (('example2.txt', PUZZLE_TEXT2),
                                   ('example3.txt', PUZZLE_TEXT3)):
        file_path = tmp_path / file_name
        file_path.write_text(puzzle_text)

    set_path = tmp_path / 'pair.flb'
    set_path.write_text('''\
        type: PuzzlePair
        puzzles:
            - example2.txt
            - example3.txt
        ''')

    puzzle_set = read_puzzle_set(set_path)

    assert isinstance(puzzle_set, PuzzlePair)
    assert len(puzzle_set.puzzles) == 2
    assert puzzle_set.puzzles[0].title == 'Example 2'
    assert puzzle_set.puzzles[1].title == 'Example 3'

def test_read_with_packing(tmp_path: Path) -> None:
    for file_name, puzzle_text in (('example1.txt', PUZZLE_TEXT1),
                                   ('example2.txt', PUZZLE_TEXT2),
                                   ('example3.txt', PUZZLE_TEXT3)):
        file_path = tmp_path / file_name
        file_path.write_text(puzzle_text)

    set_path = tmp_path / 'set.flb'
    set_path.write_text('''\
        type: PuzzleSet
        puzzles:
            - example2.txt
            - example3.txt
            - example1.txt
        packing_pages:
            - |
                AA.BB.
                AABBCC
                DDDECC
                .D.E..
                ..EEGG
                FFFGGH
                .FIIIH
                ...IHH
        ''')

    puzzle_set = read_puzzle_set(set_path)

    assert puzzle_set.block_packer.state.shape == (8, 6)

def test_read_puzzle_below(tmp_path: Path) -> None:
    child_path = tmp_path / 'child'
    child_path.mkdir()
    for file_name, puzzle_text in (('child/example2.txt', PUZZLE_TEXT2),
                                   ('example3.txt', PUZZLE_TEXT3)):
        file_path = tmp_path / file_name
        file_path.write_text(puzzle_text)

    set_path = tmp_path / 'pair.flb'
    set_path.write_text('''\
        type: PuzzlePair
        puzzles:
            - child/example2.txt
            - example3.txt
        ''')

    puzzle_set = read_puzzle_set(set_path)

    assert isinstance(puzzle_set, PuzzlePair)
    assert len(puzzle_set.puzzles) == 2
    assert puzzle_set.puzzles[0].title == 'Example 2'
    assert puzzle_set.puzzles[1].title == 'Example 3'

def test_read_puzzle_above(tmp_path: Path) -> None:
    child_path = tmp_path / 'child'
    child_path.mkdir()
    puzzle_paths = []
    for file_name, puzzle_text in (('child/example2.txt', PUZZLE_TEXT2),
                                   ('example3.txt', PUZZLE_TEXT3)):
        file_path = tmp_path / file_name
        file_path.write_text(puzzle_text)
        puzzle_paths.append(file_path)

    set_path = tmp_path / 'child/pair.flb'
    set_path.write_text('''\
        type: PuzzlePair
        puzzles:
            - example2.txt
            - ../example3.txt
        ''')

    puzzle_set = read_puzzle_set(set_path)

    assert isinstance(puzzle_set, PuzzlePair)
    assert len(puzzle_set.puzzles) == 2
    assert puzzle_set.puzzles[0].title == 'Example 2'
    assert puzzle_set.puzzles[1].title == 'Example 3'
    assert puzzle_set.puzzles[0].source_path == puzzle_paths[0]

def test_write(tmp_path: Path) -> None:
    puzzles = []
    for file_name, puzzle_text in (('example2.txt', PUZZLE_TEXT2),
                                   ('example3.txt', PUZZLE_TEXT3),
                                   ('example1.txt', PUZZLE_TEXT1)):
        file_path = tmp_path / file_name
        file_path.write_text(puzzle_text)
        puzzles.append(Puzzle.parse_path(file_path))
    block_packer = BlockPacker(start_text=dedent("""\
        AA.BB.
        AABBCC
        DDDECC
        .D.E..
        ..EEGG
        FFFGGH
        .FIIIH
        ...IHH"""))
    puzzle_set = PuzzleSet(*puzzles,
                           block_packer=block_packer,
                           start_hue=30)

    set_path = tmp_path / 'set.flb'
    expected_set_text = dedent('''\
        type: PuzzleSet
        puzzles:
        - example2.txt
        - example3.txt
        - example1.txt
        start_hue: 30
        packing_pages:
        - |-
          AA.BB.
          AABBCC
          DDDECC
          .D.E..
          ..EEGG
          FFFGGH
          .FIIIH
          ...IHH
        ''')

    write_puzzle_set(puzzle_set, set_path)

    set_text = set_path.read_text()
    assert set_text == expected_set_text

def test_write_below_puzzle(tmp_path: Path) -> None:
    child_path = tmp_path / 'child'
    child_path.mkdir()
    puzzles = []
    for file_name, puzzle_text in (('example2.txt', PUZZLE_TEXT2),
                                   ('example3.txt', PUZZLE_TEXT3),
                                   ('child/example1.txt', PUZZLE_TEXT1)):
        file_path = tmp_path / file_name
        file_path.write_text(puzzle_text)
        puzzles.append(Puzzle.parse_path(file_path))
    block_packer = BlockPacker(start_text=dedent("""\
        AA.BB.
        AABBCC
        DDDECC
        .D.E..
        ..EEGG
        FFFGGH
        .FIIIH
        ...IHH"""))
    puzzle_set = PuzzleSet(*puzzles, block_packer=block_packer)

    set_path = child_path / 'set.flb'
    expected_set_text = dedent('''\
        type: PuzzleSet
        puzzles:
        - ../example2.txt
        - ../example3.txt
        - example1.txt
        start_hue: 0
        packing_pages:
        - |-
          AA.BB.
          AABBCC
          DDDECC
          .D.E..
          ..EEGG
          FFFGGH
          .FIIIH
          ...IHH
        ''')

    write_puzzle_set(puzzle_set, set_path)

    set_text = set_path.read_text()
    assert set_text == expected_set_text
