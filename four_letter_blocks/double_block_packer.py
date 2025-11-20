from collections import Counter, defaultdict
from datetime import datetime, timedelta
from itertools import permutations

import numpy as np
from miniexact import miniexacts_x

from four_letter_blocks.block import flipped_shapes
from four_letter_blocks.puzzle import Puzzle, RotationsDisplay
from four_letter_blocks.x_packer import XPacker
from four_letter_blocks.packing_option import PackingOption


class DoubleBlockPacker:
    def __init__(self,
                 *start_texts: str) -> None:
        self.is_logging = False
        self.front_packers: list[XPacker] = []  # Before combining
        self.back_packers: list[XPacker] = []  # Before combining
        combined_start_texts = self.combine_start_texts(start_texts)
        self.front_packer = XPacker(start_text=combined_start_texts[0])
        self.width = self.front_packer.width
        self.height = self.front_packer.height
        front_unused = self.front_packer.unused_count
        self.filter_seconds = 1
        self.filter_limit = 1000

        self.back_packer = XPacker(start_text=combined_start_texts[1])
        back_unused = self.back_packer.unused_count
        if front_unused != back_unused:
            raise ValueError(
                f'Different space counts: {front_unused} and {back_unused}.')

    @property
    def state(self):
        return np.concatenate((self.front_packer.state, self.back_packer.state))

    def combine_start_texts(self, start_texts):
        start_packers = [XPacker(start_text=start_text)
                         for start_text in start_texts]
        if len(start_texts) <= 2:
            self.front_packers = start_packers[:1]
            self.back_packers = start_packers[1:]
            return start_texts
        head_packer = start_packers[0]
        split_packers = []
        for tail_packers in permutations(start_packers[1:]):
            ordered_packers = [head_packer]
            ordered_packers.extend(tail_packers)
            ordered_counts = [packer.unused_count for packer in ordered_packers]
            for front_count in range(1, len(ordered_packers)):
                front_total = sum(ordered_counts[:front_count])
                back_total = sum(ordered_counts[front_count:])
                if front_total == back_total:
                    split_packers = [ordered_packers[:front_count],
                                     ordered_packers[front_count:]]
                    break
            if split_packers:
                break

        if not split_packers:
            start_counts = tuple(packer.unused_count
                                 for packer in start_packers)
            raise ValueError(f'No combination of unused counts could be evenly '
                             f'split: {start_counts}')

        self.front_packers = split_packers[0]
        self.back_packers = split_packers[1]
        combined_start_texts = []
        max_width = max(packer.width for packer in start_packers)
        for side_packers in split_packers:
            side_text_lines = []
            for i, packer in enumerate(side_packers):
                if i > 0:
                    side_text_lines.append('#' * max_width)
                packer_lines = packer.display().splitlines()
                padding = (max_width - packer.width) * '#'
                side_text_lines.extend(line + padding for line in packer_lines)
            combined_start_texts.append('\n'.join(side_text_lines))
        return combined_start_texts

    def fill(self) -> bool:
        """ Fill both front and back with the same block shapes and rotations.

        :return: True if no gaps remain, False otherwise.
        """
        self.back_packer.is_logging = self.is_logging
        self.front_packer.is_logging = self.is_logging

        solver = miniexacts_x()
        front_options: list[PackingOption] = []
        back_options: list[PackingOption] = []
        for packers, options in ((self.front_packers, front_options),
                                 (self.back_packers, back_options)):
            row_count = 0
            for packer in packers:
                deadline = datetime.now() + timedelta(seconds=self.filter_seconds)
                # print(f'{datetime.now()} - Filtering '
                #       f'{packer.width} x {packer.height}...')
                filtered_options = packer.filter_options(deadline,
                                                         self.filter_limit)
                # print(f'Found {len(filtered_options)} options.')

                column_count = packer.width
                new_row_count = row_count + packer.height
                if row_count:
                    new_row_count += 1  # border between sections
                    filtered_options = [
                        option.resized(new_row_count, column_count)
                        for option in filtered_options]
                options.extend(filtered_options)
                row_count = new_row_count

        for prefix, packer in (('b_', self.back_packer),
                               ('f_', self.front_packer)):
            for item_name in packer.find_open_space_items():
                solver.primary(prefix + item_name)

        back_shape_map: dict[str, list[PackingOption]] = defaultdict(list)
        for option in back_options:
            shape_options = back_shape_map[option.rotated_shape_name]
            shape_options.append(option)

        flipped_shape_names = flipped_shapes()
        front_masks: dict[int, np.ndarray] = {}
        back_masks: dict[int, np.ndarray] = {}

        option_num = 0
        for front_option in front_options:
            back_shape_name = flipped_shape_names[front_option.rotated_shape_name]
            back_shape_options = back_shape_map[back_shape_name]
            for back_option in back_shape_options:
                for prefix, items in (('b_', back_option.space_items),
                                      ('f_', front_option.space_items)):
                    for space_name in items:
                        item_name = prefix + space_name
                        solver.add(item_name)
                option_num = solver.add(0)
                assert option_num != 0

                # Save option mask to assemble state from solution.
                front_masks[option_num] = front_option.mask
                back_masks[option_num] = back_option.mask

        # print(f'{datetime.now()} - Solving from {option_num} options...')
        # solver.write_to_dlx('problem.dlx')
        if solver.solve() != XPacker.SOLUTION_FOUND:
            return False

        selected_options = solver.selected_options()

        for packer, masks in ((self.back_packer, back_masks),
                              (self.front_packer, front_masks)):
            start_state = packer.state
            assert start_state is not None
            new_state = start_state.copy()
            start_block = max(int(new_state.max()), packer.GAP) + 1
            for block_num, option_num in enumerate(selected_options, start_block):
                coverage_flags = masks[option_num][:packer.height, :packer.width]
                new_state += np.uint8(block_num) * coverage_flags
            packer.state = new_state

        return True

    def count_back_shapes(self, back_state: np.ndarray) -> Counter[str]:
        block_text = self.back_packer.display(back_state)
        back_puzzle = Puzzle.parse_sections('',
                                            block_text,
                                            '',
                                            block_text)
        back_puzzle.rotations_display = RotationsDisplay.BACK
        shape_counts = back_puzzle.shape_counts
        return shape_counts

    def sort_blocks(self):
        self.front_packer.sort_blocks()
        self.back_packer.sort_blocks()

        front_blocks = defaultdict(list)
        for block_num, block in self.front_packer.create_blocks_with_block_num():
            shape = block.rotated_shape
            front_blocks[shape].append(block_num)

        flipped_shape_names = flipped_shapes()
        block_nums = []
        for block_num, block in self.back_packer.create_blocks_with_block_num():
            back_shape = block.rotated_shape
            front_shape = flipped_shape_names[back_shape]
            back_block_num = front_blocks[front_shape].pop(0)
            block_nums.append(back_block_num)
        self.back_packer.sort_blocks(block_nums)

    def display(self) -> str:
        front_display = self.front_packer.display()
        back_display = self.back_packer.display()
        return f"{front_display}\n\n{back_display}"