import typing
from collections import Counter

import numpy as np

from four_letter_blocks.block import flipped_shapes
from four_letter_blocks.block_packer import BlockPacker, build_masks


class DoubleBlockPacker:
    def __init__(self, front_text: str, back_text: str, tries: int) -> None:
        front_lines = front_text.splitlines()
        width = len(front_lines[0])
        height = len(front_lines)

        self.front_packer = BlockPacker(width,
                                        height,
                                        start_text=front_text)
        self.front_packer.force_fours = True
        front_unused = np.count_nonzero(
            self.front_packer.state == BlockPacker.UNUSED)

        self.back_packer = BlockPacker(width,
                                       height,
                                       start_text=back_text)
        self.back_packer.force_fours = True
        back_unused = np.count_nonzero(
            self.back_packer.state == BlockPacker.UNUSED)
        if front_unused != back_unused:
            raise ValueError(
                f'Different space counts: {front_unused} and {back_unused}.')

        self.front_shape_counts = self.front_packer.calculate_max_shape_counts()
        self.tries = tries
        self.is_full = False
        self.needed_block_count = front_unused // 4

    def fill(self) -> bool:
        """ Fill both front and back with the same block shapes and rotations.

        :return: True if no gaps remain, False otherwise.
        """
        if self.tries == 0:
            # print('0 tries left.')
            return False
        self.tries -= 1
        width = self.front_packer.width
        height = self.front_packer.height
        flipped_shape_names = flipped_shapes()
        front_slots = self.front_packer.find_slots()
        back_slots = self.back_packer.find_slots()
        front_coverage = self.front_packer.slot_coverage
        back_coverage = self.back_packer.slot_coverage
        front_min = front_coverage.min()
        back_min = back_coverage.min()
        if front_min == 0 or back_min == 0:
            # At least one gap with no coverage.
            # print('Gap without coverage.')
            return False
        if front_min == 255:
            # All gaps are filled.
            # print('Filled!')
            return True
        is_front_first = front_min <= back_min
        if is_front_first:
            min1 = front_min
            packer1 = self.front_packer
            packer2 = self.back_packer
            slots1 = front_slots
            slots2 = back_slots
            coverage1 = front_coverage
            coverage2 = back_coverage
        else:
            min1 = back_min
            packer1 = self.back_packer
            packer2 = self.front_packer
            slots1 = back_slots
            slots2 = front_slots
            coverage1 = back_coverage
            coverage2 = front_coverage
        mins1 = np.argwhere(coverage1 == min1)

        slot_counts = {shape1: slots1[shape1].sum()
                       for shape1 in flipped_shape_names}

        all_masks = build_masks(packer1.width, packer1.height)
        shape_scores: typing.Counter[str] = Counter()
        for shape, slot_count in slot_counts.items():
            if is_front_first:
                target_count = self.front_shape_counts[shape]
            else:
                front_shape = flipped_shape_names[shape]
                target_count = self.front_shape_counts[front_shape]
            if target_count == 0:
                continue
            # noinspection PyTypeChecker
            shape_scores[shape] = -slot_count / target_count

        start_state1 = packer1.state
        assert start_state1 is not None
        start_state2 = packer2.state
        assert start_state2 is not None
        next_block = packer1.find_next_block()
        for shape1, _score in shape_scores.most_common():
            shape2 = flipped_shape_names[shape1]
            masks1 = all_masks[shape1]
            masks2 = all_masks[shape2]
            shape1_slots = slots1[shape1]
            shape2_slots = slots2[shape2]
            all_coords1 = self.find_slot_coords(shape1_slots,
                                                masks1,
                                                mins1)
            if all_coords1.size == 0:
                continue
            slots2_masked = masks2[shape2_slots].any(axis=0)[:width, :height]
            slots2_coverage = slots2_masked * coverage2
            uncovered2 = slots2_coverage == 0
            uncovered_count = np.argwhere(uncovered2).shape[0]
            if uncovered_count == width * height:
                continue
            slots2_coverage[uncovered2] = 255
            # sort covered coordinates
            sorted_coverage2 = np.transpose(np.unravel_index(
                np.argsort(slots2_coverage, axis=None),
                slots2_coverage.shape))
            sorted_coverage2 = sorted_coverage2[:-uncovered_count]

            tried_slots2 = set()
            for row2, col2 in sorted_coverage2:
                covering_masks2 = masks2[:, :, row2, col2]
                covering_slots2 = np.logical_and(covering_masks2, shape2_slots)
                covering_coords2 = np.argwhere(covering_slots2)
                for slot_row2, slot_col2 in covering_coords2:
                    slot_index2 = (slot_row2, slot_col2)
                    if slot_index2 in tried_slots2:
                        continue
                    tried_slots2.add(slot_index2)
                    for slot_row1, slot_col1 in all_coords1:
                        mask1 = masks1[
                                     slot_row1,
                                     slot_col1,
                                     :width,
                                     :height]
                        packer1.state = start_state1 + next_block * mask1
                        mask2 = masks2[
                                    slot_row2,
                                    slot_col2,
                                    :width,
                                    :height]
                        packer2.state = start_state2 + next_block * mask2
                        # needed_blocks = self.needed_block_count - next_block + 1
                        # print(f'=== {self.tries} tries, '
                        #       f'{is_front_first=}, '
                        #       f'{needed_blocks} unfilled blocks, '
                        #       f'{min1} min coverage, '
                        #       f'index1 ({slot_row1}, {slot_col1}), '
                        #       f'index2 ({slot_row2}, {slot_col2})')
                        # print(self.display())
                        self.is_full = self.fill()
                        if self.is_full:
                            # print('Full!')
                            return True
                        if self.tries == 0:
                            # print('0 tries left.')
                            return False
                        packer1.state = start_state1
                        packer2.state = start_state2
        # print('Tried all minimum slots.')
        return False

    @staticmethod
    def find_slot_coords(shape_slots, masks, min_coverages):
        all_coords = np.ndarray((0, 2), dtype=int)
        for row, col in min_coverages:
            covering_masks = masks[:, :, row, col]
            covering_slots = np.logical_and(covering_masks, shape_slots)

            front_coords = np.argwhere(covering_slots)
            all_coords = np.concatenate((all_coords, front_coords))
        return np.unique(all_coords, axis=0)

    def sort_blocks(self):
        self.front_packer.sort_blocks()
        self.back_packer.sort_blocks()

    def display(self) -> str:
        front_display = self.front_packer.display()
        back_display = self.back_packer.display()
        return f"{front_display}\n\n{back_display}"