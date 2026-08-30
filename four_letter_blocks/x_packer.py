import typing
from dataclasses import dataclass
from datetime import datetime
from itertools import groupby
from operator import attrgetter

import numpy as np

from four_letter_blocks.block_packer import BlockPacker, build_masks
from four_letter_blocks.problem_solver import ProblemSolver, SolverAlgorithm
from four_letter_blocks.puzzle import Puzzle


@dataclass
class PackingOption:
    rotated_shape_name: str
    space_items: list[str]  # 4 item names
    mask: np.ndarray  # 1s in the 4 covered spaces


class XPacker(BlockPacker):
    def __init__(self,
                 width=0,
                 height=0,
                 start_text: str | None = None,
                 start_state: np.ndarray | None = None,
                 split_row=0):
        """ Create an instance of XPacker.

        This packer uses miniexact's DLX algorithm to find a packing.

        :param width: Width of the grid to pack
        :param height: Height of the grid to pack
        :param start_text: Text grid to start filling from
        :param start_state: Initial grid state to start filling from
        :param split_row: Index of the first row of the second section, when you
            don't want any blocks to cross between two sections
        """
        super().__init__(width,
                         height,
                         start_text=start_text,
                         start_state=start_state,
                         split_row=split_row)
        self.is_logging = False
        self.is_logging_filter = False
        self.force_fours = True
        self.timeout: float | None = None  # seconds to fill the grid.
        self.retries = 0  # Number of times to retry with shuffle after timeout.

    def fill(self) -> bool:
        """ Fill in the current state with the given shapes.

        For self.target_shape_counts and self.required_shape_counts, disables
        rotation if any of the shapes contain a letter and rotation number.
        :return: True, if self.required_shape_counts has gone to zero, or if
            it's None and no gaps are left, otherwise False.
        """
        for state in self.find_fillings():
            self.state = state
            return True
        return False

    def find_fillings(self,
                      yield_states = True) -> typing.Iterator[np.ndarray | None]:
        """ Iterate through all possible fillings.

        :param yield_states: True, if the filled states should be yielded,
            otherwise a None will be yielded as each filling is found.
        """
        start_state = self.state
        assert start_state is not None
        if self.is_full:
            if (self.target_shape_counts is None or
                    self.target_shape_counts.total() == 0):
                yield start_state
            return

        option_masks: dict[tuple[str, ...], np.ndarray] = {}  # { option_num: [[flag]] }
        try:
            solver = self.prepare_solver(option_masks)
        except ValueError:
            # No valid options, no solutions.
            if self.is_full:
                yield self.state
            return
        width = self.width
        height = self.height
        solution_count = 0
        retries = self.retries
        while True:
            solution_count += 1
            if self.is_logging:
                print(datetime.now(), f'Finding solution {solution_count}...')
            while True:
                try:
                    selected_options = solver.solve(self.timeout)
                    break
                except TimeoutError:
                    if retries <= 0:
                        raise
                    solver.shuffle()
                    retries -= 1

            if selected_options is None:
                if self.is_logging:
                    print(datetime.now(), f'Solution {solution_count} not found.')
                break
            if self.is_logging:
                print(datetime.now(), f'Found solution {solution_count}.')
            if not yield_states:
                yield None
            else:
                new_state = start_state.copy()
                block_num = max(int(new_state.max()), self.GAP) + 1
                for option_names in selected_options:
                    coverage_flags = option_masks[option_names][:height, :width]
                    square_count = coverage_flags.sum()
                    if square_count == 1:
                        multiplier = np.uint8(self.GAP)
                    else:
                        multiplier = np.uint8(block_num)
                        block_num += 1
                    new_state += multiplier * coverage_flags
                yield new_state

    def prepare_solver(
            self,
            option_masks: dict[tuple[str, ...], np.ndarray]|None = None) \
            -> ProblemSolver:
        assert self.state is not None
        is_travel_packing = self.GAP not in self.state
        if not self.target_shape_counts:
            solver = ProblemSolver(SolverAlgorithm.EXACT)
        else:
            solver = ProblemSolver(SolverAlgorithm.MULTIPLES)
            for shape_name, shape_count in self.target_shape_counts.items():
                solver.primary(shape_name, shape_count, shape_count)

        # space items are spaces in the grid, named 'i_j' for row i, column j.
        for item_name in self.find_open_space_items():
            solver.primary(item_name)

        # Each option is a slot taking up four spaces, plus a shape name.
        option_names: tuple[str, ...] | None = ()
        for option in self.find_options():
            if self.target_shape_counts:
                if option.rotated_shape_name not in self.target_shape_counts:
                    continue
                solver.add(option.rotated_shape_name)
            for item in option.space_items:
                solver.add(item)
            option_names = solver.add(0)
            assert option_names is not None

            # Save option mask to assemble state from solution.
            if option_masks is not None:
                option_masks[option_names] = option.mask

        if is_travel_packing:
            for item_option in self.find_open_space_options():
                solver.add(item_option.space_items[0])
                option_names = solver.add(0)
                assert option_names is not None

                if option_masks is not None:
                    option_masks[option_names] = item_option.mask

        if option_names is None:
            raise ValueError('No options found.')
        return solver

    def format_dlx(self, sorted_options: bool = False) -> str:
        solver = self.prepare_solver()
        dlx_text = solver.format_problem()
        if not sorted_options:
            return dlx_text
        dlx_lines = dlx_text.splitlines()
        sorted_lines = [' '.join(sorted(line.strip().split()))
                        for line in dlx_lines]
        sorted_lines[1:] = sorted(sorted_lines[1:])
        return '\n'.join(sorted_lines) + '\n'

    def find_open_space_items(self):
        open_spaces = [
            (int(i), int(j))
            for i, j in zip(*np.where(self.state == self.UNUSED))]
        for i, j in open_spaces:
            yield f'{i}_{j}'

    def find_open_space_options(self):
        open_spaces = [
            (int(i), int(j))
            for i, j in zip(*np.where(self.state == self.UNUSED))]
        no_coverage = np.zeros(shape=(self.height, self.width), dtype=bool)
        for i, j in open_spaces:
            coverage_flags = no_coverage.copy()
            coverage_flags[i, j] = True
            yield PackingOption('#',
                                [f'{i}_{j}'],
                                coverage_flags)

    def find_options(self) -> typing.Iterator[PackingOption]:
        """ Yields all options for this packer. """

        # a list of the items in each word of up to four letters, used to
        # eliminate options that cover a complete word.
        all_word_items: list[set[str]] = self.find_word_items()

        # Each option is a slot taking up four spaces, plus a shape name.
        slots = self.find_slots(self.target_shape_counts)
        all_masks = build_masks(self.width, self.height)
        for shape_name, shape_slots in slots.items():
            shape_masks = all_masks[shape_name]
            for i, row in enumerate(shape_slots):
                for j, is_available in enumerate(row):
                    if is_available:
                        coverage_flags = shape_masks[i, j]
                        covered_spaces = [
                            (int(i2), int(j2))
                            for i2, j2 in zip(*np.where(coverage_flags))]
                        block_items = {f'{i2}_{j2}'
                                       for i2, j2 in covered_spaces}
                        has_complete_word = any(
                            word_items.issubset(block_items)
                            for word_items in all_word_items
                        )
                        if has_complete_word:
                            continue

                        yield PackingOption(shape_name,
                                            list(block_items),
                                            coverage_flags)

    def find_filtered_options(self) -> list[PackingOption]:
        filtered_options = []
        start_state = self.state
        options = list(self.find_options())
        filtered_count = 0
        total_count = 0
        for rotated_shape_name, group_options in groupby(
                options,
                attrgetter('rotated_shape_name')):
            if self.is_logging_filter:
                print(f'\n{rotated_shape_name}', end='', flush=True)
            for option in group_options:
                self.state = start_state
                next_block = self.find_next_block()
                self.state = start_state + next_block * option.mask[
                    :self.height,
                    :self.width]
                try:
                    is_filled = self.fill()
                    if is_filled:
                        status = '.'
                    else:
                        status = '!'
                except TimeoutError:
                    is_filled = True
                    status = '?'
                if self.is_logging_filter:
                    print(status, end='', flush=True)
                if is_filled:
                    filtered_options.append(option)
                else:
                    filtered_count += 1
                total_count += 1
        if self.is_logging_filter:
            print(f'\nFiltered {filtered_count} options out of {total_count}, '
                  f'{total_count and filtered_count/total_count * 100 or 0:.2f}%')
        self.state = start_state
        return filtered_options

    def find_word_items(self) -> list[set[str]]:
        all_word_items: list[set[str]] = []
        start_text = self.display()
        puzzle = Puzzle.parse_sections('',
                                       start_text.replace('.', 'X'),
                                       '',
                                       start_text)
        for i in range(self.height):
            y = i + 1  # Don't remember why the grid uses 1-based x and y.
            for j in range(self.width):
                x = j + 1
                square = puzzle.grid.squares[y][x]
                if square is None:
                    continue
                for word, di, dj in ((square.across_word, 0, 1),
                                     (square.down_word, 1, 0)):
                    if word is None:
                        continue
                    if len(word) > 4:
                        continue
                    word_items = []
                    for k in range(len(word)):
                        i2 = i + k*di
                        j2 = j + k*dj
                        item_name = f'{i2}_{j2}'
                        word_items.append(item_name)
                    word_item_set = set(word_items)
                    all_word_items.append(word_item_set)
        return all_word_items