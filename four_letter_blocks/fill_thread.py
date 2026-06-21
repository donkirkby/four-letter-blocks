import typing
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QThread, Signal, QObject

from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.double_block_packer import DoubleBlockPacker
from four_letter_blocks.puzzle import Puzzle, RotationsDisplay
from four_letter_blocks.x_packer import XPacker


@dataclass(frozen=True)
class PackingProgress:
    summary: str
    target_texts: tuple[str, ...]
    source_texts: tuple[str, ...]
    # score: FitnessScore
    is_success: bool = False


class FillThread(QThread):
    """ Run evolutionary packing in a background thread. """
    status_update = Signal(PackingProgress)
    completed = Signal(PackingProgress)

    def __init__(self,
                 target_texts: typing.Sequence[str],
                 source_texts: typing.Sequence[str] = (),
                 report_path: Path | None = None,
                 parent: QObject | None = None):
        """ Initialize.

        :param target_texts: grids to pack with blocks, may be puzzle grids with
            black squares, or travel grids with no black squares that you can
            add black squares to.
        :param source_texts: either packed puzzle grids to use for required
            shape counts, or unpacked puzzle grids to pack at the same time
            with flipped shape counts. If target_texts are puzzle grids with
            black squares, then flip the shape counts.
        :param report_path: path to write report to as solutions are found. If
            it's not None, then the thread keeps running forever, otherwise it
            stops at the first solution.

        Possible scenarios:
        1. Pack one puzzle's grid. inputs: target_texts[0]
           (black squares, unpacked)
        2. Pack a travel grid with the shape counts from a puzzle. inputs:
           target_texts[0] (no black squares, unpacked),
           source_texts[0] (black squares, packed)
        3. Pack a travel grid with the shape counts from multiple puzzles. inputs:
           target_texts[0] (no black squares, unpacked),
           source_texts (black squares, packed)
        4. Pack front and back puzzles with flipped shape counts. inputs:
           target_texts (black squares, unpacked)
        """
        super().__init__(parent)
        self.target_texts = list(target_texts)
        self.source_texts = list(source_texts)
        self.report_path = report_path
        if self.source_texts:
            # Scenario 2 or 3
            start_text = self.target_texts[0].replace('.', '?')
            target_puzzle = Puzzle.parse_sections('',
                                                  start_text,
                                                  '',
                                                  start_text)
            target_puzzle.rotations_display = RotationsDisplay.FRONT
            packed_shape_counts = target_puzzle.shape_counts
            self.packer: BlockPacker|DoubleBlockPacker = XPacker(
                start_text=start_text)
            self.packer.force_fours = False

            source_puzzle = Puzzle.parse_sections('',
                                                  self.source_texts[0],
                                                  '',
                                                  self.source_texts[0])
            source_puzzle.rotations_display = RotationsDisplay.BACK
            self.packer.target_shape_counts = (source_puzzle.shape_counts -
                                               packed_shape_counts)
            # Path('problem.dlx').write_text(self.packer.format_dlx())
        elif len(self.target_texts) > 1:
            # Scenario 4
            self.packer = DoubleBlockPacker(*self.target_texts)
        # self.attempt_count = 0
        # self.top_fitness = FitnessScore(-100, -1)
        # self.solutions: list[PackingProgress] = []
        #
        # gap_count = sum(c == '.' for c in self.target_texts[0])
        # block_count = gap_count // 4
        #
        # if not source_texts:
        #     target_shape_counts = EvoPacker.calculate_target_shape_counts(
        #         block_count)
        # else:
        self.progress: PackingProgress | None = None

    def run(self):
        # if self.report_path is not None:
        #     self.pack_until_interrupted()
        #     return
        #
        # try:
        #     is_packed = self.run_epochs()
        # except RuntimeError as ex:
        #     status = f'Filling failed: {ex}'
        #     is_packed = False
        # else:
        #     if is_packed:
        #         status = 'Filled.'
        #     else:
        #         status = 'Filling failed.'
        # if not self.isInterruptionRequested():
        #     if self.source_texts is None:
        #         source_texts = None
        #     else:
        #         source_texts = tuple(self.source_texts)
        #     progress = PackingProgress(status,
        #                                tuple(self.target_texts),
        #                                source_texts,
        #                                self.packer.top_fitness,
        #                                is_packed)
        is_filled = self.packer.fill()
        if is_filled:
            summary = 'Filled.'
            if isinstance(self.packer, DoubleBlockPacker):
                target_texts = (self.packer.front_packer.display(),
                                self.packer.back_packer.display())
            else:
                target_texts = (self.packer.display(),)
        else:
            summary = 'Filling failed.'
            target_texts = tuple(self.target_texts)
        self.progress = PackingProgress(summary,
                                        target_texts,
                                        tuple(self.source_texts),
                                        is_filled)
        self.completed.emit(self.progress)

    def pack_until_interrupted(self):
        # back_start_blocks = self.back_puzzle.format_blocks().replace(
        #     '?',
        #     '.')
        # front_start_blocks = self.front_puzzle.format_blocks().replace(
        #     '?',
        #     '.')
        # with open(self.report_path, 'w') as f:
        #     print('No solutions found.', file=f)
        #     print(self.back_puzzle.title, file=f)
        #     print(back_start_blocks, file=f)
        #     print(file=f)
        #     print(self.front_puzzle.title, file=f)
        #     print(front_start_blocks, file=f)
        #
        # while not self.isInterruptionRequested():
        #     self.attempt_count += 1
        #     self.back_puzzle = Puzzle.parse_sections(
        #         self.back_puzzle.title,
        #         self.back_puzzle.format_grid(),
        #         self.back_puzzle.format_clues(),
        #         back_start_blocks)
        #     self.back_puzzle.rotations_display = RotationsDisplay.BACK
        #
        #     self.front_puzzle = Puzzle.parse_sections(
        #         self.front_puzzle.title,
        #         self.front_puzzle.format_grid(),
        #         self.front_puzzle.format_clues(),
        #         front_start_blocks)
        #     self.back_puzzle.rotations_display = RotationsDisplay.BACK
        #     self.front_puzzle.rotations_display = RotationsDisplay.FRONT
        #     packed_puzzles = self.pack_both_sides(
        #         self.front_puzzle,
        #         self.back_puzzle)
        #     if packed_puzzles is None:
        #         continue
        #     self.front_puzzle, self.back_puzzle = packed_puzzles
        #
        #     self.solutions.append((self.back_puzzle.format_blocks(),
        #                            self.front_puzzle.format_blocks(),
        #                            self.top_fitness))
        #     with open(self.report_path, 'w') as f:
        #         for i, (back_blocks,
        #                 front_blocks,
        #                 fitness) in enumerate(self.solutions):
        #             if i > 0:
        #                 print(file=f)
        #                 print('===', file=f)
        #             print(self.back_puzzle.title, file=f)
        #             print(back_blocks, file=f)
        #             print(file=f)
        #             print(self.front_puzzle.title, file=f)
        #             print(fitness, file=f)
        #             print(front_blocks, file=f)
        pass

    def pack_back_puzzle(self) -> bool:
        return False
        # back_puzzle = self.back_puzzle
        # if self.front_puzzle is None:
        #     front_blocks = '...'
        # else:
        #     front_blocks = self.front_puzzle.format_blocks()
        # self.start_text = back_puzzle.format_blocks()
        # # packed_puzzle = self.run_epochs(back_puzzle, front_blocks=front_blocks)
        # # if packed_puzzle is None:
        # #     return False
        # # self.back_puzzle = packed_puzzle
        # return True

    def pack_front_puzzle(self) -> bool:
        # packed_back_puzzle = self.back_puzzle
        # front_puzzle = self.front_puzzle
        # assert front_puzzle is not None
        # if self.packing_blocks is None:
        #     packed_shape_counts = front_puzzle.shape_counts
        #     self.start_text = front_puzzle.format_blocks()
        # else:
        #     dummy_puzzle = Puzzle.parse_sections(title='Dummy',
        #                                          grid_text=self.packing_blocks,
        #                                          clues_text='',
        #                                          blocks_text=self.packing_blocks)
        #     dummy_puzzle.rotations_display = RotationsDisplay.FRONT
        #     packed_shape_counts = dummy_puzzle.shape_counts
        #     self.start_text = self.packing_blocks
        #
        # needed_counts = packed_back_puzzle.shape_counts
        # needed_counts.subtract(packed_shape_counts)
        # min_count = min(needed_counts.values())
        # if min_count < 0:
        #     raise RuntimeError('Cannot fill with negative counts.')
        #
        # back_blocks = packed_back_puzzle.format_blocks()
        # packed_puzzle = self.run_epochs(front_puzzle, back_blocks=back_blocks)
        # if packed_puzzle is None:
        #     return False
        # self.front_puzzle = packed_puzzle
        # return True
        return False

    def run_epochs(self) -> bool:
        # packer = self.packer
        # packer.setup()
        # while (packer.current_epoch < packer.epochs and
        #        not self.isInterruptionRequested()):
        #     is_found = packer.run_epoch()
        #     new_target = packer.top_blocks
        #     if self.attempt_count:
        #         prefix = f'found {len(self.solutions)}/{self.attempt_count-1}, '
        #     else:
        #         prefix = ''
        #     status = f'Packing: {prefix}epoch {packer.current_epoch}, ' \
        #              f'{packer.top_fitness}'
        #
        #     self.target_texts[0] = new_target
        #     progress = PackingProgress(status,
        #                                tuple(self.target_texts),
        #                                tuple(self.source_texts),
        #                                packer.top_fitness,
        #                                is_found)
        #     # noinspection PyUnresolvedReferences
        #     self.status_update.emit(progress)
        #     self.top_fitness = packer.top_fitness
        #     if is_found:
        #         self.solutions.append(progress)
        #         return True
        return False

    def pack_both_sides(self,
                        front_puzzle: Puzzle,
                        back_puzzle: Puzzle) -> tuple[Puzzle, Puzzle] | None:
        """ Pack front and back puzzles together.

        :return: packed_front_puzzle, packed_back_puzzle or None if packing
            failed.
        """
        # front_text = front_puzzle.format_blocks().replace('?', '.')
        # back_text = back_puzzle.format_blocks().replace('?', '.')
        #
        # packer = DoubleEvoPacker(front_text, back_text, tries=400)
        # packer.setup(self.fitness_calculator)
        # packer.is_logging = True
        # new_front = new_back = ''
        # while packer.current_epoch < 1000:
        #     is_found = packer.run_epoch()
        #     if self.isInterruptionRequested():
        #         return None
        #     new_front, new_back = packer.top_blocks.split('\n\n')
        #
        #     status = f'Packing epoch {packer.current_epoch}, ' \
        #              f'{packer.top_fitness}'
        #
        #     # noinspection PyUnresolvedReferences
        #     self.status_update.emit(status, new_back, new_front)
        #     self.top_fitness = packer.top_fitness
        #     if is_found:
        #         break
        # else:
        #     if not packer.find_usable_packing():
        #         return None
        #
        # new_front_puzzle = Puzzle.parse_sections(
        #     front_puzzle.title,
        #     front_puzzle.format_grid(),
        #     front_puzzle.format_clues(),
        #     new_front)
        # new_back_puzzle = Puzzle.parse_sections(
        #     back_puzzle.title,
        #     back_puzzle.format_grid(),
        #     back_puzzle.format_clues(),
        #     new_back)
        # return new_front_puzzle, new_back_puzzle
        return None
