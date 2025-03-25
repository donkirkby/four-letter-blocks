""" Count up how many of each shape and rotation are needed for all puzzles. """
import argparse
from collections import Counter
from pathlib import Path

from four_letter_blocks.puzzle import Puzzle, RotationsDisplay


def parse_args():
    parser = argparse.ArgumentParser()
    default_other = Path(__file__).parent.with_name('dump')
    default_core = default_other / 'single-sided-as-is'
    default_other /= 'single-sided-other'
    parser.add_argument('core_path',
                        type=Path,
                        nargs='?',
                        default=default_core)
    parser.add_argument('other_path',
                        type=Path,
                        nargs='?',
                        default=default_other)
    return parser.parse_args()


def main():
    args = parse_args()
    shape_totals = Counter()  # Total front shapes in core folder
    shape_maxes = Counter()  # Max back shapes in other folder
    core_folder: Path = args.core_path

    print(f'Scanning total front shapes in {core_folder.name}:')
    for puzzle_path in core_folder.glob('*.txt'):
        with puzzle_path.open() as puzzle_file:
            puzzle = Puzzle.parse(puzzle_file)
        puzzle.rotations_display = RotationsDisplay.FRONT
        shape_counts = count_shapes_and_blacks(puzzle)

        shape_displays = []
        for shape, count in sorted(shape_counts.items()):
            shape_displays.append(f'{shape}: {count}')
        print(f'{puzzle.title}:\t{', '.join(shape_displays)}')
        shape_totals += shape_counts

    other_folder: Path = args.other_path
    print(f'Scanning maximum back shapes in {other_folder.name}:')
    for puzzle_path in other_folder.glob('*.txt'):
        with puzzle_path.open() as puzzle_file:
            puzzle = Puzzle.parse(puzzle_file)
        puzzle.rotations_display = RotationsDisplay.BACK
        shape_counts = count_shapes_and_blacks(puzzle)

        shape_displays = []
        for shape, count in sorted(shape_counts.items()):
            shape_maxes[shape] = max(shape_maxes[shape], count)
            shape_displays.append(f'{shape}: {count}')
        print(f'{puzzle.title}:\t{', '.join(shape_displays)}')

    print('Shape, total front, max back:')
    for shape, shape_max in sorted(shape_maxes.items()):
        shape_total = shape_totals[shape]
        suffix = '!' if shape_max > shape_total else ''
        print(f'{shape}:\t{shape_total}\t{shape_max}{suffix}')


def count_shapes_and_blacks(puzzle):
    shape_counts = puzzle.shape_counts
    total_blocks = sum(shape_counts.values())
    black_count = puzzle.grid.width * puzzle.grid.height - total_blocks * 4
    shape_counts['#'] = black_count
    return shape_counts


main()
