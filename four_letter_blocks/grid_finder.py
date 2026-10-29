import argparse
from datetime import datetime
from itertools import count

from four_letter_blocks.double_block_packer import DoubleBlockPacker
from four_letter_blocks.grid_generator import GridGenerator
from four_letter_blocks.puzzle import Puzzle


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description='Generate combinations of grids that can be double packed. '
                    'It will generate a random set of grids, try to pack them '
                    'for an hour, then generate another set, until it '
                    'successfully finds a packable set.')
    parser.add_argument('-s',
                        '--sizes',
                        type=int,
                        nargs=argparse.ONE_OR_MORE,
                        default=(7, 7),
                        help='Size of each grid to generate.')
    parser.add_argument('-l',
                        '--letter-counts',
                        type=int,
                        nargs=argparse.ONE_OR_MORE,
                        default=(44, 44),
                        help='Number of letters in each grid.')

    args = parser.parse_args()
    if len(args.sizes) != len(args.letter_counts):
        raise ValueError(
            'Number of grid sizes must match number of letter counts.')
    return args


def main() -> None:
    args = parse_args()
    for _ in count():
        print(f'{datetime.now()}: Generating layouts.')
        layouts = []
        for size, letter_count in zip(args.sizes, args.letter_counts):
            black_count = (size * size - letter_count)
            generator = GridGenerator(size, black_count)
            generator.is_logging = True
            generator.epochs = 1000
            is_generated = generator.generate()
            if not is_generated:
                raise RuntimeError(f'Could not generate a {size}x{size} grid.')
            layout = generator.top_grid
            layout_letter_count = layout.count('.')
            assert layout_letter_count == letter_count

            puzzle = Puzzle.parse_sections('',
                                           layout,
                                           '',
                                           '')
            warnings = puzzle.check_style()
            assert not warnings, warnings

            layouts.append(layout)
        print('\n===\n'.join(layouts))
        print(f'{datetime.now()}: Solving...')
        try:
            packer = DoubleBlockPacker(*layouts)
        except ValueError:
            print(f'{datetime.now()}: Solving failed to start.')
            continue

        packer.is_logging_worker = True
        packer.pool_size = 8
        packer.max_timeout_minutes = 30
        is_filled = packer.fill()
        if is_filled:
            print(packer.display())
            break
        print(f'{datetime.now()}: Solving failed.')


main()
