from pathlib import Path

import yaml

from four_letter_blocks.big_puzzle_pair import BigPuzzlePair
from four_letter_blocks.one_sided_set import OneSidedSet
from four_letter_blocks.puzzle import Puzzle
from four_letter_blocks.puzzle_pair import PuzzlePair
from four_letter_blocks.puzzle_set import PuzzleSet


def str_presenter(dumper, data):
    if len(data.splitlines()) > 1:  # check for multiline string
        return dumper.represent_scalar('tag:yaml.org,2002:str', data, style='|')
    return dumper.represent_scalar('tag:yaml.org,2002:str', data)

yaml.add_representer(str, str_presenter)


def read_puzzle_set(file_path: Path) -> PuzzleSet:
    """ Read a puzzle set from a .flb file.

    The file uses YAML format, includes a list of puzzle files to load, as well
    as other options related to the whole set of puzzles.
    """
    set_text = file_path.read_text()
    set_lines = [line
                 for line in set_text.splitlines()
                 if not line.strip().startswith('#')]
    if set_lines and not set_lines[0].strip().startswith('type:'):
        raise ValueError('Not a puzzle set file.')

    set_options = yaml.safe_load(set_text)
    set_types = {cls.__name__: cls for cls in (PuzzleSet,
                                               PuzzlePair,
                                               BigPuzzlePair,
                                               OneSidedSet)}
    set_class = set_types[set_options['type']]
    puzzles = []
    for puzzle_file_name in set_options['puzzles']:
        puzzle_path = file_path.parent / puzzle_file_name
        puzzles.append(Puzzle.parse_path(puzzle_path))
    return set_class(*puzzles, set_options=set_options)


def write_puzzle_set(puzzle_set: PuzzleSet, file_path: Path) -> None:
    puzzles = [str(puzzle.source_path.relative_to(file_path.parent,
                                                  walk_up=True))
               for puzzle in puzzle_set.puzzles
               if puzzle.source_path is not None]
    packing_pages = []
    for block_packer in puzzle_set.page_packers:
        packing_pages.append(block_packer.display())
    set_options = {'type': type(puzzle_set).__name__,
                   'puzzles': puzzles,
                   'start_hue': puzzle_set.start_hue,
                   'packing_pages': packing_pages}

    file_path.write_text(yaml.dump(set_options, sort_keys=False))
