from collections import Counter, defaultdict

import numpy as np

from four_letter_blocks.block import flipped_shapes
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.puzzle import Puzzle, RotationsDisplay
from four_letter_blocks.x_packer import XPacker


class DoubleBlockPacker:
    def __init__(self,
                 front_text: str | None = None,
                 back_text: str | None = None,
                 tries: int = -1,
                 start_state: np.ndarray | None = None) -> None:
        if start_state is None:
            front_state = back_state = None
        else:
            full_height = start_state.shape[0]
            front_state = start_state[:full_height//2]
            back_state = start_state[full_height//2:]
        self.front_packer = XPacker(start_text=front_text,
                                    start_state=front_state)
        self.width = self.front_packer.width
        self.height = self.front_packer.height
        front_unused = np.count_nonzero(
            self.front_packer.state == BlockPacker.UNUSED)

        self.back_packer = XPacker(start_text=back_text, start_state=back_state)
        back_unused = np.count_nonzero(
            self.back_packer.state == BlockPacker.UNUSED)
        if front_unused != back_unused:
            raise ValueError(
                f'Different space counts: {front_unused} and {back_unused}.')

        self.tries = tries
        self.is_full = False
        self.are_slots_shuffled = False
        self.needed_block_count = front_unused // 4

    @property
    def state(self):
        return np.concatenate((self.front_packer.state, self.back_packer.state))

    def fill(self) -> bool:
        """ Fill both front and back with the same block shapes and rotations.

        :return: True if no gaps remain, False otherwise.
        """
        start_shape_counts = self.count_back_shapes(self.back_packer.state)
        for back_state in self.back_packer.find_fillings():
            shape_counts = (self.count_back_shapes(back_state) -
                            start_shape_counts)
            self.front_packer.min_shape_counts = shape_counts
            self.front_packer.max_shape_counts = shape_counts
            if self.front_packer.fill():
                self.back_packer.state = back_state
                return True
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