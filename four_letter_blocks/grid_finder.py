import argparse
from datetime import datetime
from itertools import count
from multiprocessing import Process, Queue

from four_letter_blocks.double_block_packer import DoubleBlockPacker
from four_letter_blocks.grid_generator import generator_loop


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
    queue: Queue[list[str]] = Queue(maxsize=1)
    generator_process = Process(target=generator_loop,
                                args=(args.sizes, args.letter_counts, queue))
    generator_process.start()
    for _ in count():
        start_time = datetime.now()
        print(f'{start_time}: Generating layouts.')
        layouts = queue.get()
        duration = datetime.now() - start_time
        print('\n===\n'.join(layouts))
        print(f'{datetime.now()}: Generated in {duration}, solving...')
        try:
            packer = DoubleBlockPacker(*layouts)
        except ValueError:
            print(f'{datetime.now()}: Solving failed to start.')
            continue

        packer.is_logging_worker = True
        packer.pool_size = 7  # Leave 1 core for generating grids.
        packer.max_timeout_minutes = 60
        is_filled = packer.fill()
        if is_filled:
            print(packer.display())
            break
        print(f'{datetime.now()}: Solving failed.')

    generator_process.terminate()


main()
