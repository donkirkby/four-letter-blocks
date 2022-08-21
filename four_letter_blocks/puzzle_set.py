import math
import typing
from collections import Counter, defaultdict

from four_letter_blocks.puzzle import Puzzle


class PuzzleSet:
    def __init__(self, *puzzles: Puzzle):
        self.puzzles = puzzles
        self.shape_counts: typing.Counter[str] = Counter()

        total_counts = Counter()
        max_counts = Counter()
        max_puzzles = {}  # {combo: index}
        source_puzzles = defaultdict(list)  # {combo: [index]}
        combos = {'J': 'JL', 'L': 'JL', 'S': 'SZ', 'Z': 'SZ'}
        pairs = {}
        for pair in combos.values():
            first, last = pair
            pairs[first] = last
            pairs[last] = first
        for i, puzzle in enumerate(self.puzzles):
            puzzle_counts = Counter()
            for label, count in puzzle.shape_counts.items():
                combo = combos.get(label, label)
                puzzle_counts[combo] += count
                if combo != label:
                    puzzle_counts[label] += count
            total_counts += puzzle_counts
            for combo, count in puzzle_counts.items():
                source_puzzles[combo].append(i)
                if count > max_counts[combo]:
                    max_counts[combo] = count
                    max_puzzles[combo] = i
        extras = []
        for combo, total_count in sorted(total_counts.items()):
            max_count = max_counts[combo]
            mirror = pairs.get(combo)
            source_nums = ', '.join(str(i + 1)
                                    for i in source_puzzles[combo])
            if mirror is None:
                extra = 2*max_count - total_count
                if extra > 0:
                    extras.append(f'{combo}: {extra}({max_puzzles[combo]+1})')
                elif total_count % 2 != 0:
                    extras.append(f'{combo}: 1({source_nums})')
            else:
                mirror_count = total_counts[mirror]
                extra = total_count - mirror_count
                if extra > 0:
                    extras.append(f'{combo}: {extra}({source_nums})')
            if len(combo) == 1:
                self.shape_counts[combo] = max(math.ceil(total_count/2),
                                               max_count)

        if extras:
            self.block_summary = 'Extras: ' + ', '.join(extras)
        else:
            self.block_summary = ''
