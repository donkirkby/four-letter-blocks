import typing
from collections import Counter
from datetime import datetime
from pathlib import Path
from tempfile import NamedTemporaryFile

import numpy as np
from miniexact import miniexacts_m

from four_letter_blocks.block import Block
from four_letter_blocks.block_packer import BlockPacker, build_masks
from four_letter_blocks.packing_option import PackingOption
from four_letter_blocks.puzzle import Puzzle


class XPacker(BlockPacker):
    SOLUTION_FOUND = 10
    SOLUTION_NOT_FOUND = 20

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

    def find_fillings(self,
                      yield_states = True) -> typing.Iterator[np.ndarray | None]:
        start_state = self.state
        assert start_state is not None
        option_map: dict[int, PackingOption] = {}  # { option_num: option }
        solver = self.prepare_solver(option_map)
        width = self.width
        height = self.height
        solution_count = 0
        while True:
            solution_count += 1
            if self.is_logging:
                print(datetime.now(), f'Finding solution {solution_count}...')
            if solver.solve() != self.SOLUTION_FOUND:
                if self.is_logging:
                    print(datetime.now(), f'Solution {solution_count} not found.')
                break
            if self.is_logging:
                print(datetime.now(), f'Found solution {solution_count}.')
            if not yield_states:
                yield None
            else:
                selected_options = solver.selected_options()
                new_state = start_state.copy()
                start_block = max(int(new_state.max()), self.GAP) + 1
                for block_num, option_num in enumerate(selected_options, start_block):
                    option = option_map[option_num]
                    coverage_flags = option.mask[:height, :width]
                    new_state += np.uint8(block_num) * coverage_flags
                yield new_state

    def prepare_solver(
            self,
            option_map: dict[int, PackingOption]|None = None) -> miniexacts_m:
        # space items are spaces in the grid, named 'i_j' for row i, column j.
        solver = miniexacts_m()
        for item_name in self.find_open_space_items():
            solver.primary(item_name)

        # self.add_shape_items(solver)

        # Each option is a slot taking up four spaces, plus a shape name.
        for option in self.find_options():
            # solver.add(option.rotated_shape_name[0])
            for item in option.space_items:
                solver.add(item)
            option_num = solver.add(0)
            assert option_num != 0

            # Save option mask to assemble state from solution.
            if option_map is not None:
                option_map[option_num] = option
        return solver

    def format_dlx(self, sorted_options: bool = False) -> str:
        solver = self.prepare_solver()
        with NamedTemporaryFile(suffix='.dlx', delete_on_close=False) as tmp:
            tmp.close()
            filename = tmp.name
            solver.write_to_dlx(filename)
            dlx_text = Path(filename).read_text()
            if not sorted_options:
                return dlx_text
            dlx_lines = dlx_text.splitlines()
            sorted_lines = []
            for i, line in enumerate(dlx_lines):
                if i == 0:
                    sorted_lines.append(line)
                else:
                    items = line.split()
                    items.sort()
                    sorted_line = ' '.join(items)
                    sorted_lines.append(sorted_line)
            return '\n'.join(sorted_lines)

    def add_shape_items(self, solver: miniexacts_m) -> None:
        """ Add an item to the solver for each shape.

        If self.required_shape_counts is set, then exact multiplicities will
        be set for rotated shape names.
        Otherwise, plain shape names will be set with multiplicity ranges.
        :param solver: receives the items with multiplicity
        :return: the set of used rotated shape names
        """

        if self.required_shape_counts:
            for shape_name, shape_count in self.required_shape_counts.items():
                solver.primary(shape_name, shape_count, shape_count)
        else:
            space_count = self.unused_count
            block_count = space_count // 4
            max_shape_count = block_count # // 7 + 2
            min_shape_count = 0
            # Shape items use the shape name, plus minimum and maximum counts.
            # Shape items ignore rotation.
            for shape_name in Block.shape_names():
                solver.primary(shape_name, min_shape_count, max_shape_count)

    def find_open_space_items(self):
        open_spaces = [
            (int(i), int(j))
            for i, j in zip(*np.where(self.state == self.UNUSED))]
        for i, j in open_spaces:
            yield f's{i}_{j}'

    def find_options(self) -> typing.Iterator[PackingOption]:
        """ Yields all options for this packer. """

        # a list of the items in each word of up to four letters, used to
        # eliminate options that cover a complete word.
        all_word_items: list[set[str]] = self.find_word_items()

        # Each option is a slot taking up four spaces, plus a shape name.
        slots = self.find_slots()
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
                        block_items = {f's{i2}_{j2}'
                                       for i2, j2 in covered_spaces}
                        has_complete_word = any(
                            word_items.issubset(block_items)
                            for word_items in all_word_items
                        )
                        if has_complete_word:
                            continue

                        yield PackingOption(shape_name,
                                            coverage_flags)
                                            # list(block_items))


    def filter_options(self,
                       deadline: datetime | None = None,
                       limit = 1000) -> list[PackingOption]:
        option_map: dict[int, PackingOption] = {}  # { option_num: option }
        solver = self.prepare_solver(option_map)
        filtered_options = set()  # option numbers
        option_counts: Counter[int] = Counter()  # option numbers
        while True:
            if solver.solve() != self.SOLUTION_FOUND:
                break
            if deadline is not None and deadline < datetime.now():
                break
            selected_options = solver.selected_options()
            if not filtered_options:
                # Always include the first solution, so we have at least one.
                filtered_options = set(selected_options)
            option_counts.update(selected_options)

        for option_num, option_count in option_counts.most_common(limit):
            if len(filtered_options) >= limit:
                break
            filtered_options.add(option_num)
        return [option_map[option_num] for option_num in filtered_options]

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
                        item_name = f's{i2}_{j2}'
                        word_items.append(item_name)
                    word_item_set = set(word_items)
                    all_word_items.append(word_item_set)
        return all_word_items