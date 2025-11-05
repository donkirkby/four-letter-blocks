import typing
from pathlib import Path

import numpy as np
from PySide6.QtCore import QThread, Signal, QObject

from four_letter_blocks.puzzle import Puzzle
from four_letter_blocks.x_packer import XPacker


class PageFillThread(QThread):
    """ Run evolutionary packing in a background thread.

    Possible scenarios: pack one puzzle's grid, pack another puzzle's grid with
    the flipped shape counts from the first puzzle's packing, pack a travel grid
    with the shape counts from a puzzle, pack front and back puzzles with the
    same shape counts.
    """
    status_update = Signal(str, str, str)  # status, back_blocks, front_blocks
    completed = Signal(bool, str, Puzzle, Puzzle)  # success, summary, back, front

    def __init__(self,
                 parent: QObject | None,
                 page_packer: XPacker,
                 report_path: Path | None = None):
        super().__init__(parent)
        # self.page_packer = page_packer
        # self.report_path = report_path
        # total_block_count = 0
        # if page_packer.required_shape_counts:
        #     total_block_count = page_packer.required_shape_counts.total()
        # if page_packer.target_shape_counts:
        #     fitness_calculator.count_targets.update(page_packer.target_shape_counts)
        #     total_block_count = page_packer.target_shape_counts.total()
        # empty_coords: tuple[np.ndarray] = np.nonzero(
        #     page_packer.state == 0)  # type: ignore
        # empty_spaces = empty_coords[0].size
        # self.fitness_calculator.min_empty_spaces = (empty_spaces -
        #                                             total_block_count*4)
        #
        # self.attempt_count: int = 0
        # self.top_fitness: FitnessScore = FitnessScore(-100, -1)
        #
        # # [(packing, fitness)]
        # self.solutions: typing.List[typing.Tuple[str, FitnessScore]] = []

    def run(self):
        self.pack_until_interrupted()

    def pack_until_interrupted(self):
        pass
        # start_blocks = self.page_packer.display()
        # with open(self.report_path, 'w') as f:
        #     print('No solutions found.', file=f)
        #     print(start_blocks, file=f)
        #     print(file=f)
        #
        # # noinspection PyUnresolvedReferences
        # while not self.isInterruptionRequested():
        #     self.attempt_count += 1
        #
        #     if not self.run_epochs():
        #         # Failed to fill, no solution found.
        #         continue
        #     self.solutions.append((self.page_packer.display(),
        #                            self.top_fitness))
        #     with self.report_path.open('w') as f:
        #         for i, (display, fitness) in enumerate(self.solutions):
        #             if i > 0:
        #                 print(file=f)
        #                 print('===', file=f)
        #             print(display, file=f)
        #             print(file=f)
        #             print(fitness, file=f)

    def run_epochs(self) -> bool:
        """ Run a set of evolutionary epochs. Return True on success. """
        # packer = self.page_packer
        # packer.setup(self.fitness_calculator)
        # while packer.current_epoch < 1000:
        #     is_found = packer.run_epoch()
        #     if self.isInterruptionRequested():
        #         return False
        #     new_display = packer.top_blocks
        #     if self.attempt_count:
        #         prefix = f'found {len(self.solutions)}/{self.attempt_count-1}, '
        #     else:
        #         prefix = ''
        #     status = f'Packing: {prefix}epoch {packer.current_epoch}, ' \
        #              f'{packer.top_fitness}'
        #
        #     # noinspection PyUnresolvedReferences
        #     self.status_update.emit(status, new_display, '')
        #     self.top_fitness = packer.top_fitness
        #     if is_found:
        #         return True
        return False
