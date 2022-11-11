from collections import Counter
from pathlib import Path

from four_letter_blocks.evo_packer import EvoPacker
from four_letter_blocks.puzzle import Puzzle


def main():
    path = Path(__file__).parent.parent / 'dump' / 'next-13x13b.txt'
    with path.open() as f:
        puzzle = Puzzle.parse(f)

    packer = EvoPacker(13, 13, start_text=puzzle.format_blocks())
    packer.epochs = 10_000
    packer.is_logging = True
    packer.fill(Counter({shape: 33 for shape in 'IOJLSZT'}))
    print(packer.display())


main()
