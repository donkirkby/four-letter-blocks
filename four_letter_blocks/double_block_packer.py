from collections import Counter, defaultdict
from datetime import datetime
from itertools import permutations

import numpy as np

from four_letter_blocks.block import flipped_shapes
from four_letter_blocks.puzzle import Puzzle, RotationsDisplay
from four_letter_blocks.x_packer import XPacker


class DoubleBlockPacker:
    def __init__(self,
                 *start_texts: str) -> None:
        self.is_logging = False
        combined_start_texts = self.combine_start_texts(start_texts)
        self.front_packer = XPacker(start_text=combined_start_texts[0])
        self.width = self.front_packer.width
        self.height = self.front_packer.height
        front_unused = self.front_packer.unused_count

        self.back_packer = XPacker(start_text=combined_start_texts[1])
        back_unused = self.back_packer.unused_count
        if front_unused != back_unused:
            raise ValueError(
                f'Different space counts: {front_unused} and {back_unused}.')

    @property
    def state(self):
        return np.concatenate((self.front_packer.state, self.back_packer.state))

    @staticmethod
    def combine_start_texts(start_texts):
        if len(start_texts) <= 2:
            return start_texts
        start_packers = [XPacker(start_text=start_text)
                         for start_text in start_texts]
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
        assert self.back_packer.state is not None
        start_shape_counts = self.count_back_shapes(self.back_packer.state)
        if self.is_logging:
            print(datetime.now(), 'Filling back...')
            print(self.back_packer.display())
        seen_counts = set()
        # display_packer = XPacker(self.back_packer.width, self.back_packer.height)
        for back_state in self.back_packer.find_fillings():
            assert back_state is not None
            shape_counts = (self.count_back_shapes(back_state) -
                            start_shape_counts)
            shape_counts_text = ', '.join(
                f'{shape}: {n}' for shape, n in sorted(shape_counts.items()))
            if shape_counts_text in seen_counts:
                if self.is_logging:
                    print('.', end='', flush=True)
                continue
            seen_counts.add(shape_counts_text)
            if self.is_logging:
                print()
                # display_packer.state = back_state
                # display_packer.sort_blocks()
                # sorted_display = display_packer.display()
                # print(sorted_display)
                print(datetime.now(), shape_counts_text)
            self.front_packer.required_shape_counts = shape_counts
            if self.front_packer.fill():
                self.back_packer.state = back_state
                return True
            # if self.is_logging:
            #     print("Couldn't fill.")
        return False

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