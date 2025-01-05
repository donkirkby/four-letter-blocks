import math
import typing
from collections import defaultdict, Counter
from functools import cache
from random import shuffle

import numpy as np
from scipy.ndimage import label  # type: ignore

from four_letter_blocks.block import shape_rotations, normalize_coordinates, Block
from four_letter_blocks.square import Square


class BlockPacker:
    """ Scenarios we use this for:
    * Packing a set of two different size puzzles, shape counts are given,
      black squares can be freely placed.
    * Packing a puzzle with max shape counts.
    * Packing a puzzle grid with exact shape counts (sum of max counts = space).
    """
    UNUSED = 0
    GAP = 1

    def __init__(self,
                 width=0,
                 height=0,
                 tries=-1,
                 min_tries=-1,
                 start_text: str | None = None,
                 start_state: np.ndarray | None = None,
                 split_row=0):
        self.state: np.ndarray | None
        if start_state is not None:
            self.height, self.width = start_state.shape
            self.state = start_state
        elif start_text is None:
            self.width = width
            self.height = height
            self.state = np.zeros((height, width), np.uint8)
        else:
            lines = start_text.splitlines()
            self.height = len(lines)
            self.width = self.height and len(lines[0])
            self.state = np.ndarray((self.height, self.width), np.int8)
            for row, line in enumerate(lines):
                for col, char in enumerate(line):
                    self.state[row, col] = (0 if char == '.'
                                            else 1 if char == '#'
                                            else ord(char) - 63)
        self.split_row = split_row
        self.force_fours = False
        self.tries = tries
        self.stop_tries = 0
        if 0 <= min_tries < tries:
            self.stop_tries = tries - min_tries
        self.is_tracing = False

        # True if slots should be filled in random order, otherwise False if
        # slots should be filled from top to bottom.
        self.are_slots_shuffled = False

        # True if self.state should be set, even with a partial filling
        self.are_partials_saved = False

        self.fewest_unused: int | None = None
        self.slot_coverage = self.state

    @property
    def positions(self):
        result = defaultdict(list)
        shape_map = shape_rotations()
        max_block = np.max(self.state)
        for block in range(2, max_block+1):
            # convert row, col to x, y
            y_coordinates, x_coordinates = np.nonzero(self.state == block)
            coordinates = list(zip(x_coordinates, y_coordinates))
            norm_coordinates = normalize_coordinates(coordinates)  # type: ignore
            shape_name, rotation = shape_map[norm_coordinates]
            result[shape_name].append((min(x_coordinates),
                                       min(y_coordinates),
                                       rotation))
        return result

    @property
    def rotated_positions(self):
        rotated_positions = defaultdict(list)
        for shape, shape_positions in self.positions.items():
            for x, y, rotation in shape_positions:
                if shape == 'O':
                    rotated_shape = shape
                else:
                    rotated_shape = f'{shape}{rotation}'
                rotated_positions[rotated_shape].append((x, y))
        return rotated_positions

    @property
    def is_full(self):
        if self.state is None:
            return False
        # noinspection PyUnresolvedReferences
        return not (self.state == 0).any()

    def calculate_max_shape_counts(self):
        """ Calculate how many of each shape and rotation should be packed.

        This tries to get a roughly even number of each shape, plus a few extras
        to make packing more flexible.
        """
        # noinspection PyUnresolvedReferences
        block_count = (self.state == 0).sum() // 4
        block_count += 7  # Add flexibility to make packing easier.
        multiplier = {'O': 4, 'S': 2, 'Z': 2, 'I': 2}
        shape_names = Block.shape_rotation_names()
        return {shape: math.ceil(multiplier.get(shape[0], 1) * block_count / 28)
                for shape in shape_names}

    def find_slots(self) -> dict[str, np.ndarray]:
        """ Find slots where each shape rotation can fit.

        If you allow rotations, you have to combine the slots for each rotation.
        Any spaces that are already filled have coverage 255.
        :return: {shape: bitmap}
        """
        if self.state is None:
            raise RuntimeError('Cannot find slots with invalid state.')

        # Track spaces that are already filled, or how many slots cover them.
        non_gaps = self.state.astype(bool)
        slot_coverage = non_gaps.astype(np.uint8) * 255
        all_masks = build_masks(self.width, self.height)
        shape_heights = get_shape_heights()
        slots = {}
        padded = np.pad(non_gaps, (0, 3), constant_values=1)
        for shape, masks in all_masks.items():
            collisions = np.logical_and(masks, padded)
            colliding_positions = np.any(collisions, axis=(2, 3))

            # Check for rows that cross the split row.
            shape_height = shape_heights[shape]
            crossing_positions = np.zeros_like(colliding_positions)
            crossing_positions[
                self.split_row-shape_height+1:self.split_row, :] = True

            open_slots = np.logical_not(np.logical_or(colliding_positions,
                                                      crossing_positions))

            if not self.force_fours:
                usable_slots = open_slots
            else:
                gaps = np.logical_not(np.logical_or(masks, padded))
                structure = np.zeros((3, 3, 3, 3), bool)
                structure[1, 1, :, :] = [[0, 1, 0],
                                         [1, 1, 1],
                                         [0, 1, 0]]
                gap_groups, group_count = label(gaps, structure=structure)
                bin_counts = np.bincount(gap_groups.flatten())
                uneven_groups, = np.nonzero(bin_counts % 4)
                if uneven_groups.size and uneven_groups[0] == 0:
                    uneven_groups = uneven_groups[1:]
                is_uneven = np.isin(gap_groups, uneven_groups)
                has_even = np.logical_not(np.any(is_uneven, axis=(2, 3)))

                usable_slots = np.logical_and(open_slots, has_even)
            usable_masks = masks[usable_slots]
            shape_coverage = usable_masks[:, :self.height, :self.width].sum(
                axis=0, dtype=np.uint8)
            slot_coverage += shape_coverage
            slots[shape] = usable_slots
        self.slot_coverage = slot_coverage
        if self.are_partials_saved or slot_coverage.all():
            return slots

        # Some unfilled spaces weren't covered by any usable slots, return empty.
        return {}

    def display(self, state: np.ndarray | None = None) -> str:
        if state is None:
            state = self.state
        assert state is not None
        ascii_offset = 63  # Displays first block as A.
        last_block = np.amax(state) + ascii_offset
        if last_block >= 127:
            raise RuntimeError('Too many blocks for text display.')

        return '\n'.join(
            ''.join(chr(ascii_offset+c) if c > 1 else c and '#' or '.'
                    for c in row)
            for row in state)

    def sort_blocks(self):
        state = np.zeros(self.state.shape, np.uint8)
        gap_spaces = self.state == 1
        state += gap_spaces
        next_block = 2
        for row in range(state.shape[0]):
            for col in range(state.shape[1]):
                new_block = state[row, col]
                if new_block != 0:
                    # already filled as part of a block
                    continue
                old_block = self.state[row, col]
                if old_block <= 1:
                    # gap or space
                    continue
                # noinspection PyUnresolvedReferences
                block_spaces = (self.state == old_block).astype(np.uint8)
                state += next_block * block_spaces
                next_block += 1
        self.state = state

    def create_blocks(self) -> typing.Iterable[Block]:
        assert self.state is not None
        max_block = np.max(self.state)
        for block_num in range(2, max_block + 1):
            try:
                block = self.create_block(block_num)
            except ValueError:
                continue
            yield block

    def create_blocks_with_block_num(self) -> typing.Iterable[
            typing.Tuple[int, Block]]:
        assert self.state is not None
        max_block = np.max(self.state)
        for block_num in range(2, max_block + 1):
            try:
                block = self.create_block(block_num)
            except ValueError:
                continue
            yield block_num, block

    def create_block(self, block_num):
        coordinates = np.column_stack(np.nonzero(self.state == block_num))
        if coordinates.size == 0:
            raise ValueError(f'No blocks have value {block_num}.')
        squares = []
        for row, col in coordinates:
            square = Square('X')
            square.x = col
            square.y = row
            squares.append(square)
        block = Block(*squares)
        return block

    def fill(self, shape_counts: typing.Counter[str]) -> bool:
        """ Fill in the current state with the given shapes.

        Cycles through the available shapes in shape_counts, and tries them in
        different positions, looking for the fewest rows. Set the current state
        to a filled in copy, not changing the original.

        Slots with least coverage are always filled first. If
        self.are_slots_shuffled is True, then coverage ties are broken randomly,
        otherwise ties are filled from top to bottom.

        If self.are_partials_saved is True, then we don't cycle through options,
        just make the first choice for each slot and return with self.state set.

        :param shape_counts: number of blocks of each shape, disables rotation
            if any of the shapes contain a letter and rotation number. Adjusted
            to remaining counts, if self.are_partials_saved is True.
        :return: True, if successful, otherwise False.
        """
        are_slots_shuffled = self.are_slots_shuffled
        are_partials_saved = self.are_partials_saved
        if self.tries == 0:
            self.state = None
            return False
        if self.tries > 0:
            self.tries -= 1
        best_state = None
        assert self.state is not None
        start_state = self.state
        if not sum(shape_counts.values()):
            # Nothing to add!
            best_state = start_state
        next_block = self.find_next_block()
        fewest_rows = start_state.shape[0]+1

        slots = self.find_slots()
        is_rotation_allowed = all(len(shape) == 1 for shape in shape_counts)
        raw_slot_counts = {shape: shape_slots.sum()
                           for shape, shape_slots in slots.items()}
        if not is_rotation_allowed:
            slot_counts = raw_slot_counts
        else:
            slot_counts = Counter()
            for shape, slot_count in raw_slot_counts.items():
                slot_counts[shape[0]] += slot_count

        shape_scores: typing.Counter[str] = Counter()
        for shape, slot_count in slot_counts.items():
            target_count = shape_counts[shape]
            if target_count == 0:
                continue
            if slot_count == 0 and are_partials_saved:
                # Don't try shape with no slots, but don't give up, either.
                continue
            # noinspection PyTypeChecker
            shape_scores[shape] = -slot_count / target_count
        for shape, _score in shape_scores.most_common():
            if not is_rotation_allowed:
                slot_shapes = [shape]
            else:
                slot_shapes = [slot_shape
                               for slot_shape in slots.keys()
                               if slot_shape.startswith(shape)]
            old_count = shape_counts[shape]
            shape_counts[shape] = old_count - 1
            for rotated_shape in slot_shapes:
                slot_rows, slot_cols = np.nonzero(slots[rotated_shape])
                if len(slot_rows) == 0:
                    continue
                slot_indexes = list(range(len(slot_rows)))
                if are_slots_shuffled:
                    shuffle(slot_indexes)
                for slot_index in slot_indexes:
                    # noinspection PyTypeChecker
                    target_row: int = slot_rows[slot_index]
                    # noinspection PyTypeChecker
                    target_col: int = slot_cols[slot_index]

                    self.state = start_state
                    for new_state in self.place_block(rotated_shape,
                                                      target_row,
                                                      target_col,
                                                      next_block):
                        self.state = new_state
                        unused_count = np.count_nonzero(self.state == self.UNUSED)
                        if (self.fewest_unused is None or
                                unused_count < self.fewest_unused):
                            self.fewest_unused = unused_count
                        is_filled = unused_count == 0
                        remaining_pieces_count = sum(shape_counts.values())
                        is_finished = is_filled or remaining_pieces_count == 0
                        if self.is_tracing:
                            print(f'{unused_count} unused '
                                  f'with {self.tries} tries left, '
                                  f'finished? {is_finished}')
                            print(self.display())
                        if not is_finished and self.tries != 0:
                            is_filled = self.fill(shape_counts)
                            if not is_filled:
                                continue
                        used_rows = self.count_filled_rows()
                        if used_rows < fewest_rows:
                            best_state = self.state
                            fewest_rows = used_rows
                        if 0 <= self.tries <= self.stop_tries and best_state is not None:
                            break
                        if are_partials_saved:
                            break
                    if 0 <= self.tries <= self.stop_tries and best_state is not None:
                        break
                    if are_partials_saved:
                        break
                if 0 <= self.tries <= self.stop_tries and best_state is not None:
                    break
                if are_partials_saved:
                    break
            if 0 <= self.tries <= self.stop_tries and best_state is not None:
                break
            if are_partials_saved:
                break
            shape_counts[shape] = old_count
        # if ((not is_rotation_allowed or best_state is None) and
        #         not are_partials_saved):
        #     return False
            # new_state = start_state.copy()
            # # noinspection PyUnboundLocalVariable
            # new_state[target_row, target_col] = 1  # gap
            # self.state = new_state
            # if self.fill(shape_counts, are_slots_shuffled, are_partials_saved):
            #     used_rows = self.count_filled_rows()
            #     if used_rows < fewest_rows:
            #         best_state = self.state
        if best_state is not None:
            self.state = best_state
            return True
        if not are_partials_saved:
            self.state = None
        return False

    def find_next_block(self) -> int:
        used_blocks = np.unique(self.state)  # type: ignore
        block: int
        for i, block in enumerate(used_blocks[:-1]):
            if block >= self.GAP and used_blocks[i + 1] != block + 1:
                next_block = block + 1
                break
        else:
            next_block = used_blocks[-1] + 1
            if next_block == self.GAP:
                next_block += 1
            elif next_block > 255:
                raise ValueError('Maximum 254 blocks in packer.')
        return next_block

    def place_block(self,
                    shape_name: str,
                    target_row: int,
                    target_col: int,
                    block_num: int):
        """ Try to place the block at the given target

        :param shape_name: name of the shape to place. If it's a single letter,
        try all possible rotations. If it's a letter and number, only use
        the rotation given by the number
        :param target_row: row to try placing the block at
        :param target_col: column to try placing the block at (top-left)
        :param block_num: block value to place in the state
        :return: an iterator of states for each successful placement
        """
        assert self.state is not None
        start_state = self.state
        blocks = shape_coordinates()
        if len(shape_name) == 1:
            allowed_blocks = blocks[shape_name]
        else:
            assert len(shape_name) == 2
            rotation = int(shape_name[1])
            allowed_blocks = blocks[shape_name[0]][rotation:rotation + 1]
        for block in allowed_blocks:
            new_state = start_state.copy()
            start_col = target_col
            end_col = target_col + block.shape[1]
            end_row = target_row + block.shape[0]
            if target_row < self.split_row < end_row:
                continue
            target = new_state[target_row:end_row, start_col:end_col]
            if target.shape != block.shape:
                # hanging over the edge
                continue
            collisions = np.logical_and(block, target)
            if collisions.any():
                continue
            target += block_num * block
            yield new_state

    def count_filled_rows(self):
        filled = np.nonzero(self.state > self.GAP)
        if not filled[0].size:
            used_rows = 0
        else:
            used_rows = filled[0][-1] + 1
        return used_rows

    def random_fill(self, shape_counts: typing.Counter[str]):
        """ Randomly place pieces from shape_counts on empty spaces. """
        self.are_slots_shuffled = True
        self.are_partials_saved = False
        self.fill(shape_counts)

    def flip(self) -> 'BlockPacker':
        assert self.state is not None
        flipped_state = np.copy(np.fliplr(self.state))
        return BlockPacker(start_state=flipped_state, tries=self.tries)


@cache
def shape_coordinates() -> typing.Dict[str, typing.List[np.ndarray]]:
    coordinate_lists = defaultdict(list)
    for coordinates, (name, rotation) in shape_rotations().items():
        max_x = max(x for x, y in coordinates)
        max_y = max(y for x, y in coordinates)
        grid = np.zeros((max_y+1, max_x+1), np.uint8)
        for x, y in coordinates:
            grid[y, x] = 1
        coordinate_lists[name].append(grid)
    return dict(coordinate_lists)


@cache
def build_masks(width: int, height: int) -> dict[str, np.ndarray]:
    """ Build the masks for each shape in each position.

    :return: {shape_name: mask_array}, where mask_array is a four-dimensional
        array of occupied spaces with index (start_row, start_col, row, col). In
        other words, if the shape starts at (start_row, start_col), is
        (row, col) filled? (start_row, start_col) is the top-left corner of
        the shape, not the first occupied space in the top row.
    """
    all_coordinates = shape_coordinates()
    all_masks = {}
    for shape, coordinate_list in all_coordinates.items():
        for rotation, start_mask in enumerate(coordinate_list):
            if len(coordinate_list) == 1:
                name = shape
            else:
                name = f'{shape}{rotation}'
            masks = np.zeros((height, width, height+3, width+3),
                             dtype=bool)
            mask_height, mask_width = start_mask.shape
            for row in range(height):
                for col in range(width):
                    masks[row,
                          col,
                          row:row+mask_height,
                          col:col+mask_width] = start_mask
            all_masks[name] = masks

    return all_masks


@cache
def get_shape_heights() -> dict[str, int]:
    shape_heights = {}
    all_coordinates = shape_coordinates()
    for shape_name, coordinate_list in all_coordinates.items():
        for rotation, shape in enumerate(coordinate_list):
            if len(coordinate_list) == 1:
                full_name = shape_name
            else:
                full_name = f'{shape_name}{rotation}'
            shape_heights[full_name] = shape.shape[0]
    return shape_heights
