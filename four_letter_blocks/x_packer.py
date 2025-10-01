import typing
from collections import Counter
from datetime import datetime

import numpy as np
from miniexact import miniexacts_m

from four_letter_blocks.block_packer import BlockPacker, build_masks
from four_letter_blocks.puzzle import Puzzle

SOLUTION_FOUND = 10
SOLUTION_NOT_FOUND = 20


class XPacker(BlockPacker):
    def __init__(self,
                 width=0,
                 height=0,
                 tries=-1,
                 min_tries=-1,
                 start_text: str | None = None,
                 start_state: np.ndarray | None = None,
                 split_row=0):
        """ Create an instance of BlockPacker.

        :param width: Width of the grid to pack
        :param height: Height of the grid to pack
        :param tries: Maximum number of cycles to try finding a block that will
            fit
        :param min_tries: Minimum number of cycles to try finding a block that
            will fit
        :param start_text: Text grid to start filling from
        :param start_state: Initial grid state to start filling from
        :param split_row: Index of the first row of the second section, when you
            don't want any blocks to cross between two sections
        """
        super().__init__(width,
                         height,
                         tries,
                         min_tries,
                         start_text,
                         start_state,
                         split_row)
        self.is_logging = False
        self.force_fours = True
        self.max_shape_counts = self.calculate_max_shape_counts()
        self.min_shape_counts: Counter[str] = Counter()
        for shape_name, max_shape_count in self.max_shape_counts.items():
            self.min_shape_counts[shape_name] = max((max_shape_count-1) // 2, 0)

    def fill(self) -> bool:
        """ Fill in the current state with the given shapes.

        Cycles through the available shapes in self.target_shape_counts or
        self.required_shape_counts, and tries them in different positions,
        looking for the fewest rows. Set the current state to a filled in copy,
        not changing the original.

        Slots with the least coverage are always filled first. If
        self.are_slots_shuffled is True, then coverage ties are broken randomly,
        otherwise ties are filled from top to bottom.

        For self.target_shape_counts and self.required_shape_counts, disables
        rotation if any of the shapes contain a letter and rotation number. They
        are adjusted to remaining counts, if self.are_partials_saved is True. If
        both are None, then calls calculate_max_shape_counts() to set
        self.target_shape_counts.
        :return: True, if self.required_shape_counts has gone to zero, or if
            it's None and no gaps are left, otherwise False.
        """
        for state in self.find_fillings():
            self.state = state
            return True
        return False

    def find_fillings(self) -> typing.Iterator[np.ndarray]:
        width = self.width
        height = self.height
        start_state = self.state
        all_word_items: list[set[str]] = self.find_word_items()
        # items are spaces in the grid, converted to an integer as
        # row*width + column.
        # Each option is a slot taking up four spaces.
        solver = miniexacts_m()
        open_spaces = [
            (int(i), int(j))
            for i, j in zip(*np.where(self.state == self.UNUSED))]
        for i, j in open_spaces:
            item_name = f'{i},{j}'
            solver.primary(item_name)
        for shape_name, max_shape_count in self.max_shape_counts.items():
            min_shape_count = self.min_shape_counts[shape_name]
            if max_shape_count > 0:
                solver.primary(shape_name, min_shape_count, max_shape_count)

        slots = self.find_slots()
        option_masks = {}  # { option_num: [[flag]] }
        all_masks = build_masks(width, height)
        for shape_name, shape_slots in slots.items():
            if self.max_shape_counts[shape_name] == 0:
                continue
            shape_masks = all_masks[shape_name]
            for i, row in enumerate(shape_slots):
                for j, is_available in enumerate(row):
                    if is_available:
                        coverage_flags = shape_masks[i, j]
                        covered_spaces = [
                            (int(i2), int(j2))
                            for i2, j2 in zip(*np.where(coverage_flags))]
                        block_items = {f'{i2},{j2}'
                                       for i2, j2 in covered_spaces}
                        has_complete_word = any(
                            word_items.issubset(block_items)
                            for word_items in all_word_items
                        )
                        if has_complete_word:
                            continue

                        for item_name in block_items:
                            solver.add(item_name)
                        solver.add(shape_name)
                        option_num = solver.add(0)  # Finish option
                        option_masks[option_num] = coverage_flags
        solution_count = 0
        while True:
            solution_count += 1
            if self.is_logging:
                print(datetime.now(), f'Finding solution {solution_count}...')
            if solver.solve() != SOLUTION_FOUND:
                if self.is_logging:
                    print(datetime.now(), f'Solution {solution_count} not found.')
                break
            if self.is_logging:
                print(datetime.now(), f'Found solution {solution_count}.')
            selected_options = solver.selected_options()
            new_state = start_state.copy()
            start_block = max(int(new_state.max()), self.GAP) + 1
            for block_num, option_num in enumerate(selected_options, start_block):
                coverage_flags = option_masks[option_num][:height, :width]
                new_state += np.uint8(block_num) * coverage_flags
            yield new_state

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
                        item_name = f'{i2},{j2}'
                        word_items.append(item_name)
                    word_item_set = set(word_items)
                    all_word_items.append(word_item_set)
        return all_word_items