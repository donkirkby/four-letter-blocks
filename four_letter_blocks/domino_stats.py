from collections import Counter
from pathlib import Path

from four_letter_blocks.domino_packer import DominoPacker


def count_dominoes(grid_lines: list[str], size: int, horizontal_counts: Counter[str], vertical_counts: Counter[str]):
    for i in range(size):
        for j in range(size):
            letter1 = grid_lines[i][j]
            if i < size - 1:
                letter2 = grid_lines[i + 1][j]
                domino = letter1 + letter2
                if '#' not in domino:
                    vertical_counts[domino] += 1
            if j < size - 1:
                letter2 = grid_lines[i][j + 1]
                domino = letter1 + letter2
                if '#' not in domino:
                    horizontal_counts[domino] += 1


def print_top_dominoes(size: int,
                       horizontal_counts: Counter[str],
                       vertical_counts: Counter[str]) -> tuple[list[str], list[str]]:
    top_dominoes: list[list[str]] = []
    domino_limit = round(size * size * 0.3)
    for title, counts in (('horizontal', horizontal_counts),
                          ('vertical', vertical_counts)):
        print(title)
        chosen_dominoes: list[str] = []
        for domino, count in counts.most_common()[:domino_limit]:
            print(domino)
            chosen_dominoes.append(domino)
        top_dominoes.append(chosen_dominoes)
    return top_dominoes[0], top_dominoes[1]


def main() -> None:
    size = 5
    path = Path(__file__).parent.parent / "dump" / f"generated{size}x{size}.log"
    log_text = path.read_text()
    sections = log_text.split("="*10)
    vertical_counts: Counter[str] = Counter()
    horizontal_counts: Counter[str] = Counter()
    good_grids: list[list[str]] = []
    for section in sections:
        if 'Qxw failed' in section:
            continue
        lines = section.strip().splitlines()
        grid_lines = lines[2:]
        if not grid_lines:
            continue
        good_grids.append(grid_lines)
    for grid_lines in good_grids:
        count_dominoes(grid_lines, size, horizontal_counts, vertical_counts)
    top_horizontal, top_vertical = print_top_dominoes(size,
                                                      horizontal_counts,
                                                      vertical_counts)
    used_options: set[str] = set()
    packed_puzzles: set[str] = set()
    packed_count = 0
    for grid_lines in good_grids:
        grid_text = '\n'.join(grid_lines)
        if grid_text in packed_puzzles:
            continue
        packer = DominoPacker(grid_text, top_horizontal, top_vertical)
        if packer.fill():
            packed_puzzles.add(grid_text)
            if packed_count != 0:
                print('='*10)
            packed_count += 1
            print(packer.display())
            used_options.update(packer.used_options)
    print(sorted(used_options))
    print(f'{packed_count} puzzles, using {len(used_options)} tiles.')


if __name__ in ('__main__', '__live_coding__'):
    main()
