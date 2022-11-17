import typing
from collections import Counter
from pathlib import Path

from PySide6.QtCore import QThread, Signal, QObject

from four_letter_blocks.block import Block
from four_letter_blocks.evo_packer import EvoPacker, PackingFitnessCalculator
from four_letter_blocks.puzzle import Puzzle


class FillThread(QThread):
    status_update = Signal(str, str, str)  # status, back_blocks, front_blocks
    completed = Signal(bool, str, Puzzle, Puzzle)  # success, summary, back, front

    def __init__(self,
                 parent: QObject | None,
                 back_puzzle: Puzzle,
                 front_puzzle: Puzzle,
                 is_packing_back: bool,
                 report_path: Path | None = None,
                 fitness_calculator: PackingFitnessCalculator = None):
        super().__init__(parent)
        # copy puzzles, so we don't access them from two threads.
        self.back_puzzle = Puzzle.parse_sections(back_puzzle.title,
                                                 back_puzzle.format_grid(),
                                                 back_puzzle.format_clues(),
                                                 back_puzzle.format_blocks())
        if front_puzzle is None:
            self.front_puzzle = None
        else:
            self.front_puzzle = Puzzle.parse_sections(
                front_puzzle.title,
                front_puzzle.format_grid(),
                front_puzzle.format_clues(),
                front_puzzle.format_blocks())
        self.is_packing_back = is_packing_back
        self.report_path = report_path
        if fitness_calculator is None:
            self.fitness_calculator = PackingFitnessCalculator()
        else:
            self.fitness_calculator = fitness_calculator
        self.attempt_count = 0
        self.solutions = []

    def run(self):
        if self.report_path is not None:
            self.pack_until_interrupted()
            return

        if self.is_packing_back:
            is_packed = self.pack_back_puzzle()
            if is_packed:
                status = 'Filled back.'
            else:
                status = 'Filling back failed.'
        else:
            try:
                is_packed = self.pack_front_puzzle()
            except RuntimeError as ex:
                status = f'Filling front failed: {ex}'
                is_packed = False
            else:
                if is_packed:
                    status = 'Filled front.'
                else:
                    status = 'Filling front failed.'
        if not self.isInterruptionRequested():
            # noinspection PyUnresolvedReferences
            self.completed.emit(is_packed,
                                status,
                                self.back_puzzle,
                                self.front_puzzle)

    def pack_until_interrupted(self):
        back_start_blocks = self.back_puzzle.format_blocks()
        front_start_blocks = self.front_puzzle.format_blocks()
        with open(self.report_path, 'w') as f:
            print('No solutions found.', file=f)
            print(self.back_puzzle.title, file=f)
            print(back_start_blocks, file=f)
            print(file=f)
            print(self.front_puzzle.title, file=f)
            print(front_start_blocks, file=f)

        while not self.isInterruptionRequested():
            self.attempt_count += 1
            self.back_puzzle = Puzzle.parse_sections(
                self.back_puzzle.title,
                self.back_puzzle.format_grid(),
                self.back_puzzle.format_clues(),
                back_start_blocks)
            if not self.pack_back_puzzle():
                continue

            self.front_puzzle = Puzzle.parse_sections(
                self.front_puzzle.title,
                self.front_puzzle.format_grid(),
                self.front_puzzle.format_clues(),
                front_start_blocks)
            if not self.pack_front_puzzle():
                continue

            self.solutions.append((self.back_puzzle.format_blocks(),
                                   self.front_puzzle.format_blocks()))
            with open(self.report_path, 'w') as f:
                for i, (back_blocks, front_blocks) in enumerate(self.solutions):
                    if i > 0:
                        print(file=f)
                        print('===', file=f)
                    print(self.back_puzzle.title, file=f)
                    print(back_blocks, file=f)
                    print(file=f)
                    print(self.front_puzzle.title, file=f)
                    print(front_blocks, file=f)

    def pack_back_puzzle(self) -> bool:
        back_puzzle = self.back_puzzle
        block_count = back_puzzle.grid.letter_count // 4
        back_shapes = Counter({shape_name: block_count
                               for shape_name in Block.shape_names()})
        if self.front_puzzle is None:
            front_blocks = '...'
        else:
            front_blocks = self.front_puzzle.format_blocks()
        packed_puzzle = self.run_epochs(
            back_puzzle,
            back_shapes,
            front_blocks=front_blocks)
        if packed_puzzle is None:
            return False
        self.back_puzzle = packed_puzzle
        return True

    def pack_front_puzzle(self) -> bool:
        packed_back_puzzle = self.back_puzzle
        front_puzzle = self.front_puzzle
        needed_counts = packed_back_puzzle.flipped_shape_counts
        needed_counts.subtract(front_puzzle.shape_counts)
        min_count = min(needed_counts.values())
        if min_count < 0:
            raise RuntimeError('Cannot fill with negative counts.')

        back_blocks = packed_back_puzzle.format_blocks()
        packed_puzzle = self.run_epochs(
            front_puzzle,
            needed_counts,
            back_blocks=back_blocks)
        if packed_puzzle is None:
            return False
        self.front_puzzle = packed_puzzle
        return True

    def run_epochs(self,
                   puzzle: Puzzle,
                   shape_counts: typing.Counter[str],
                   back_blocks: str | None = None,
                   front_blocks: str | None = None) -> Puzzle | None:
        start_text = puzzle.format_blocks().replace('?', '.')

        packer = EvoPacker(start_text=start_text)
        packer.setup(shape_counts)
        while packer.current_epoch < 1000:
            is_found = packer.run_epoch()
            if self.isInterruptionRequested():
                return
            if front_blocks is None:
                side = 'front'
                new_back = back_blocks
                new_front = packer.top_blocks
            else:
                side = 'back'
                new_back = packer.top_blocks
                new_front = front_blocks
            if self.attempt_count:
                prefix = f'found {len(self.solutions)}/{self.attempt_count-1}, '
            else:
                prefix = ''
            status = f'Packing {side}: {prefix}epoch {packer.current_epoch}, ' \
                     f'{packer.top_fitness}'

            # noinspection PyUnresolvedReferences
            self.status_update.emit(status, new_back, new_front)
            if is_found:
                break
        else:
            if not packer.find_usable_packing():
                return

        return Puzzle.parse_sections(puzzle.title,
                                     puzzle.format_grid(),
                                     puzzle.format_clues(),
                                     packer.display())
