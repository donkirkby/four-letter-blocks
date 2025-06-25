import typing
from collections import Counter
from pathlib import Path

from PySide6.QtCore import QThread, Signal, QObject

from four_letter_blocks.block import Block
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.evo_packer import EvoPacker, PackingFitnessCalculator, FitnessScore
from four_letter_blocks.puzzle import Puzzle, RotationsDisplay


class PageFillThread(QThread):
    status_update = Signal(str, str, str)  # status, back_blocks, front_blocks
    completed = Signal(bool, str, Puzzle, Puzzle)  # success, summary, back, front

    def __init__(self,
                 parent: QObject | None,
                 page_packer: BlockPacker,
                 report_path: Path | None = None):
        super().__init__(parent)
        self.page_packer = page_packer
        self.report_path = report_path
        fitness_calculator = PackingFitnessCalculator()
        if page_packer.required_shape_counts:
            fitness_calculator.count_min.update(page_packer.required_shape_counts)
        if page_packer.target_shape_counts:
            fitness_calculator.count_targets.update(page_packer.target_shape_counts)
        self.fitness_calculator = PackingFitnessCalculator()
        self.attempt_count = 0
        self.top_fitness = FitnessScore(-100, -1)

        # [(packing, fitness)]
        self.solutions: typing.List[typing.Tuple[str, str, FitnessScore]] = []

    def run(self):
        self.pack_until_interrupted()

    def pack_until_interrupted(self):
        start_blocks = self.page_packer.display()
        with open(self.report_path, 'w') as f:
            print('No solutions found.', file=f)
            print(start_blocks, file=f)
            print(file=f)

        while not self.isInterruptionRequested():
            self.attempt_count += 1
            self.back_puzzle = Puzzle.parse_sections(
                self.back_puzzle.title,
                self.back_puzzle.format_grid(),
                self.back_puzzle.format_clues(),
                back_start_blocks)
            self.back_puzzle.rotations_display = RotationsDisplay.BACK
            if not self.pack_back_puzzle():
                continue

            self.front_puzzle = Puzzle.parse_sections(
                self.front_puzzle.title,
                self.front_puzzle.format_grid(),
                self.front_puzzle.format_clues(),
                front_start_blocks)
            self.back_puzzle.rotations_display = RotationsDisplay.BACK
            self.front_puzzle.rotations_display = RotationsDisplay.FRONT
            if not self.pack_front_puzzle():
                continue

            self.solutions.append((self.back_puzzle.format_blocks(),
                                   self.front_puzzle.format_blocks(),
                                   self.top_fitness))
            with open(self.report_path, 'w') as f:
                for i, (back_blocks,
                        front_blocks,
                        fitness) in enumerate(self.solutions):
                    if i > 0:
                        print(file=f)
                        print('===', file=f)
                    print(self.back_puzzle.title, file=f)
                    print(back_blocks, file=f)
                    print(file=f)
                    print(self.front_puzzle.title, file=f)
                    print(fitness, file=f)
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
        assert front_puzzle is not None
        needed_counts = packed_back_puzzle.shape_counts
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
        packer.setup(self.fitness_calculator)
        while packer.current_epoch < 1000:
            is_found = packer.run_epoch()
            if self.isInterruptionRequested():
                return None
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
            self.top_fitness = packer.top_fitness
            if is_found:
                break
        else:
            if not packer.find_usable_packing():
                return None

        return Puzzle.parse_sections(puzzle.title,
                                     puzzle.format_grid(),
                                     puzzle.format_clues(),
                                     packer.display())
