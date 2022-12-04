import typing
from collections import defaultdict
from functools import cache

import numpy as np

from four_letter_blocks.block import shape_rotations, normalize_coordinates, Block
from four_letter_blocks.square import Square


class BlockPacker:
    UNUSED = 0
    GAP = 1

    def __init__(self,
                 width=0,
                 height=0,
                 tries=-1,
                 min_tries=-1,
                 start_text: str = None,
                 start_state: np.ndarray = None,
                 split_row=0):
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
        self.tries = tries
        self.stop_tries = 0
        if 0 <= min_tries < tries:
            self.stop_tries = tries - min_tries

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

    def display(self, state: np.ndarray = None) -> str:
        if state is None:
            state = self.state
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
                block_spaces = (self.state == old_block).astype(np.uint8)
                state += next_block * block_spaces
                next_block += 1
        self.state = state

    def create_blocks(self, with_block_num=False) -> typing.Iterable[Block]:
        max_block = np.max(self.state)
        for block_num in range(2, max_block + 1):
            try:
                block = self.create_block(block_num)
            except ValueError:
                continue
            if with_block_num:
                yield block_num, block
            else:
                yield block

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

        :param shape_counts: number of blocks of each shape, disables rotation
            if any of the shapes contain a letter and rotation number
        :return: True, if successful, otherwise False.
        """
        if self.tries == 0:
            self.state = None
            return False
        if self.tries > 0:
            self.tries -= 1
        best_state = None
        start_state = self.state
        empty = np.nonzero(self.state == 0)
        if len(empty[0]) == 0:
            # No empty spaces left, fail.
            self.state = None
            return False
        target_row = empty[0][0]
        target_col = empty[1][0]
        next_block = np.amax(start_state) + 1
        if next_block == self.GAP:
            next_block += 1
        elif next_block > 255:
            raise ValueError('Maximum 254 blocks in packer.')

        has_shapes = False
        is_rotation_allowed = True
        fewest_rows = start_state.shape[0]+1
        for shape_name, _ in shape_counts.most_common():
            old_count = shape_counts[shape_name]
            if old_count == 0:
                continue
            has_shapes = True
            shape_counts[shape_name] = old_count - 1
            if len(shape_name) > 1:
                is_rotation_allowed = False
            self.state = start_state
            for new_state in self.place_block(shape_name,
                                              target_row,
                                              target_col,
                                              next_block):
                self.state = new_state
                if sum(shape_counts.values()):
                    self.fill(shape_counts)
                    if self.state is None:
                        continue
                used_rows = self.count_filled_rows()
                if used_rows < fewest_rows:
                    best_state = self.state
                    fewest_rows = used_rows
                if 0 <= self.tries <= self.stop_tries and best_state is not None:
                    break
            shape_counts[shape_name] = old_count
            if 0 <= self.tries <= self.stop_tries and best_state is not None:
                break
        if not has_shapes:
            return True
        if not is_rotation_allowed or best_state is None:
            new_state = start_state.copy()
            new_state[target_row, target_col] = 1  # gap
            self.state = new_state
            if self.fill(shape_counts):
                used_rows = self.count_filled_rows()
                if used_rows < fewest_rows:
                    best_state = self.state
        if best_state is not None:
            self.state = best_state
            return True
        self.state = None
        return False

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
        :param target_col: column to try placing the block at
        :param block_num: block value to place in the state
        :return: an iterator of states for each successful placement
        """
        start_state = self.state
        blocks = shape_coordinates()
        if len(shape_name) == 1:
            allowed_blocks = blocks[shape_name]
        else:
            assert len(shape_name) == 2
            rotation = int(shape_name[1])
            allowed_blocks = blocks[shape_name[0]][rotation:rotation + 1]
        for block in allowed_blocks:
            first_square_index = np.where(block[0])[0][0]
            new_state = start_state.copy()
            start_col = target_col
            end_col = target_col + block.shape[1]
            if start_col >= first_square_index:
                start_col -= first_square_index
                end_col -= first_square_index
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
        filled = np.nonzero(self.state != 0)
        if not filled[0].size:
            used_rows = 0
        else:
            used_rows = filled[0][-1] + 1
        return used_rows

    def random_fill(self, shape_counts: typing.Counter[str]):
        """ Randomly place pieces from shape_counts on empty spaces. """
        empty = np.argwhere(self.state == 0)
        np.random.shuffle(empty)
        used_blocks = np.unique(self.state)
        for i, block in enumerate(used_blocks[:-1]):
            if block >= self.GAP and used_blocks[i+1] != block+1:
                next_block = block + 1
                break
        else:
            next_block = used_blocks[-1] + 1
            if next_block == self.GAP:
                next_block += 1
        shape_items = list((shape, count)
                           for shape, count in shape_counts.items()
                           if count > 0)
        if not shape_items:
            return
        np.random.shuffle(shape_items)
        for shape, count in shape_items:
            for row, col in empty:
                for new_state in self.place_block(shape, row, col, next_block):
                    shape_counts[shape] -= 1
                    self.state = new_state
                    self.random_fill(shape_counts)
                    return

    def flip(self) -> 'BlockPacker':
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
