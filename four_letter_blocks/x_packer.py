import numpy as np
from miniexact import miniexacts_x

from four_letter_blocks.block_packer import BlockPacker, build_masks

SOLUTION_FOUND = 10
SOLUTION_NOT_FOUND = 20


class XPacker(BlockPacker):
    def fill(self) -> bool:
        """ Fill in the current state with the given shapes.

        Cycles through the available shapes in self.target_shape_counts or
        self.required_shape_counts, and tries them in different positions,
        looking for the fewest rows. Set the current state to a filled in copy,
        not changing the original.

        Slots with the least coverage are always filled first. If
        self.are_slots_shuffled is True, then coverage ties are broken randomly,
        otherwise ties are filled from top to bottom.

        If self.are_partials_saved is True, then we don't cycle through options,
        just make the first choice for each slot and return with self.state set.

        For self.target_shape_counts and self.required_shape_counts, disables
        rotation if any of the shapes contain a letter and rotation number. They
        are adjusted to remaining counts, if self.are_partials_saved is True. If
        both are None, then calls calculate_max_shape_counts() to set
        self.target_shape_counts.
        :return: True, if self.required_shape_counts has gone to zero, or if
            it's None and no gaps are left, otherwise False.
        """
        width = self.width
        height = self.height
        # items are spaces in the grid, converted to an integer as
        # row*width + column.
        # Each option is a slot taking up four spaces.
        solver = miniexacts_x()
        open_spaces = [
            (int(i), int(j))
            for i, j in zip(*np.where(self.state == self.UNUSED))]
        for i, j in open_spaces:
            item_name = f'{i},{j}'
            solver.primary(item_name)

        slots = self.find_slots()
        option_masks = {}  # { option_num: [[flag]] }
        all_masks = build_masks(width, height)
        for shape_name, shape_slots in slots.items():
            shape_masks = all_masks[shape_name]
            for i, row in enumerate(shape_slots):
                for j, is_available in enumerate(row):
                    if is_available:
                        coverage_flags = shape_masks[i, j]
                        covered_spaces = [
                            (int(i2), int(j2))
                            for i2, j2 in zip(*np.where(coverage_flags))]
                        for i2, j2 in covered_spaces:
                            item_name = f'{i2},{j2}'
                            solver.add(item_name)
                        option_num = solver.add(0)  # Finish option
                        option_masks[option_num] = coverage_flags
        result = solver.solve()
        if result == SOLUTION_NOT_FOUND:
            return False
        assert result == SOLUTION_FOUND
        selected_options = solver.selected_options()
        start_block = max(int(self.state.max()), self.GAP) + 1
        for block_num, option_num in enumerate(selected_options, start_block):
            coverage_flags = option_masks[option_num][:width, :height]
            self.state += np.uint8(block_num) * coverage_flags
        return True

