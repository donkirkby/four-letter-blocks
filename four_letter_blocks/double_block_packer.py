import typing
from collections import Counter, defaultdict
from dataclasses import dataclass
from itertools import permutations

import numpy as np
from miniexact import miniexacts_x
from scipy.ndimage import label

from four_letter_blocks.block import flipped_shapes
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.puzzle import Puzzle, RotationsDisplay
from four_letter_blocks.x_packer import XPacker, PackingOption


class DoubleBlockPacker:
    def __init__(self,
                 *start_texts: str,
                 titles: list[str] | None = None) -> None:
        """ Initialise a double block packer.

        It generates all valid combinations of a front block and a back block
        that are mirror images of each other, then passes the DLX problem to
        miniexact.

        :param start_texts: a sequence of packing strings that need to be packed
        with blocks. It will split them up evenly between front and back.
        :param titles: the titles of the puzzles to pack, in the same order as
        start_texts.
        """
        self.is_logging = False
        self.titles = titles or []
        self.start_packers: list[XPacker] = []
        self.packing_targets: list[PackingTarget] = []
        self.front_text, self.back_text = self.combine_start_texts(start_texts)
        self.front_packer = XPacker(start_text=self.front_text)
        self.width = self.front_packer.width
        self.height = self.front_packer.height

        self.back_packer = XPacker(start_text=self.back_text)

        self.validate_complete_words(start_texts)
        self.validate_block_sizes()
        self.validate_unused_sizes()
        self.validate_fill_sides()
        self.validate_missing_shapes()
        self.validate_unused_totals()

    def validate_complete_words(self, start_texts: tuple[str, ...]) -> None:
        complete_word_messages: list[str] = []
        for start_text, title in zip(start_texts, self.titles):
            puzzle = Puzzle.parse_sections('',
                                           start_text,
                                           '',
                                           start_text)
            complete_word_messages.extend(
                f'{message} in {title}'
                for message in puzzle.check_word_length()
                if 'complete' in message)
        if complete_word_messages:
            raise ValueError(f'Found {", ".join(complete_word_messages)}.')

    def validate_unused_totals(self):
        front_unused = self.front_packer.unused_count
        back_unused = self.back_packer.unused_count
        if front_unused != back_unused:
            raise ValueError(
                f'Different space counts: {front_unused} and {back_unused}.')

    def validate_missing_shapes(self):
        assert self.front_packer.target_shape_counts is None
        assert self.back_packer.target_shape_counts is None

        front_shape_counts = self.front_packer.packed_shape_counts
        back_shape_counts = self.count_back_shapes(self.back_packer.state)
        missing_back_counts = front_shape_counts - back_shape_counts
        missing_front_counts = back_shape_counts - front_shape_counts
        missing_messages = [f'shape {flipped_shapes()[shape_name]} in back'
                            for shape_name in missing_back_counts.keys()]
        missing_messages.extend(f'shape {shape_name} in front'
                                for shape_name in missing_front_counts.keys())
        if missing_messages:
            raise ValueError(f"Missing {', '.join(missing_messages)}.")

    def validate_fill_sides(self) -> None:
        fill_failure_messages = []
        for packer, title in zip(self.start_packers, self.titles):
            assert packer.state is not None
            start_state = packer.state.copy()
            is_filled = packer.fill()
            if not is_filled:
                fill_failure_messages.append(f'in {title}')
            packer.state = start_state
        if fill_failure_messages:
            raise ValueError(f'Fill failed {" and ".join(fill_failure_messages)}.')

    def validate_unused_sizes(self) -> None:
        group_messages: list[str] = []
        for packer, title in zip(self.start_packers, self.titles):
            unused = packer.state == XPacker.UNUSED
            structure = np.array([[0, 1, 0],
                                  [1, 1, 1],
                                  [0, 1, 0]],
                                 bool)
            unused_groups: np.ndarray
            labeled = label(unused, structure=structure)
            assert isinstance(labeled, tuple)
            unused_groups, group_count = labeled
            bin_counts = np.bincount(unused_groups.flatten())
            uneven_groups, = np.nonzero(bin_counts % 4)
            if uneven_groups.size and uneven_groups[0] == 0:
                uneven_groups = uneven_groups[1:]
            if len(uneven_groups) == 1:
                continue
            uneven_sizes = [int(bin_counts[group_num])
                            for group_num in uneven_groups]
            uneven_sizes.sort()
            group_messages.extend(f'{size} in {title}'
                                  for size in uneven_sizes)
        if group_messages:
            raise ValueError(f'Bad unused sizes of {", ".join(group_messages)}.')

    def validate_block_sizes(self):
        front_block_sizes = np.bincount(self.front_packer.state.reshape(
            self.front_packer.width * self.front_packer.height))
        back_block_sizes = np.bincount(self.back_packer.state.reshape(
            self.back_packer.width * self.back_packer.height))
        size_messages = [f'{XPacker.BLOCK_CHARS[block]} in back'
                         for block, size in enumerate(back_block_sizes)
                         if block > XPacker.GAP and size not in (0, 4)]
        size_messages.extend(f'{XPacker.BLOCK_CHARS[block]} in front'
                             for block, size in enumerate(front_block_sizes)
                             if block > XPacker.GAP and size not in (0, 4))
        if size_messages:
            raise ValueError(f'Bad block size for {", ".join(size_messages)}.')

    @property
    def state(self):
        return np.concatenate((self.front_packer.state, self.back_packer.state))

    def combine_start_texts(self, start_texts: typing.Sequence[str]) -> list[str]:
        """ Combine all start texts into two: front side and back side.

        :param start_texts: target packing grids, in any order, of mixed sizes
        :return: [front_text, back_text]
        """
        if not self.titles:
            for start_text in start_texts:
                lines = start_text.splitlines()
                height = len(lines)
                width = len(lines[0])
                title = f'{width}x{height}'
                self.titles.append(title)
            title_totals = Counter(self.titles)
            title_counts: Counter[str] = Counter()
            for i, title in enumerate(self.titles):
                if title_totals[title] > 1:
                    title_suffix = chr(ord('A') + title_counts[title])
                    new_title = f'{title} {title_suffix}'
                    self.titles[i] = new_title
                    title_counts[title] += 1

        start_packers = [XPacker(start_text=start_text)
                         for start_text in start_texts]
        self.start_packers = start_packers

        if not start_texts:
            return ['', '']

        head_packer = start_packers[0]
        split_packers = []
        has_valid_gap_counts = False
        for tail_packers in permutations(start_packers[1:]):
            ordered_packers = [head_packer]
            ordered_packers.extend(tail_packers)
            ordered_gap_counts = [packer.unused_count
                                  for packer in ordered_packers]
            ordered_shape_counts = [packer.packed_shape_counts
                                    for packer in ordered_packers]
            for front_count in range(1, len(ordered_packers)):
                front_gap_total = sum(ordered_gap_counts[:front_count])
                back_gap_total = sum(ordered_gap_counts[front_count:])
                front_shape_counts = sum(ordered_shape_counts[:front_count],
                                         start=Counter())
                back_shape_counts = sum(ordered_shape_counts[front_count:],
                                        start=Counter())
                flipped_back_shape_counts = {
                    flipped_shapes()[shape]: shape_count
                    for shape, shape_count in back_shape_counts.items()
                }
                if front_gap_total == back_gap_total:
                    has_valid_gap_counts = True
                    if front_shape_counts == flipped_back_shape_counts:
                        split_packers = [ordered_packers[:front_count],
                                         ordered_packers[front_count:]]
                        break
            if split_packers:
                break

        if not split_packers:
            if not has_valid_gap_counts:
                extra_diff = extra_counts_text = ''
            else:
                extra_diff = ' and shape counts'
                extra_counts = []
                for packer, title in zip(start_packers,
                                         self.titles):
                    shape_items = packer.packed_shape_counts.items()
                    packer_text = ', '.join(
                        f'{shape}: {n}'
                        for shape, n in sorted(shape_items))
                    extra_counts.append(f'{packer_text} in {title}')

                extra_counts_text = '; ' + '; '.join(extra_counts)
            start_counts = tuple(
                f'{packer.unused_count} in {title}'
                for packer, title in zip(start_packers,
                                         self.titles))
            raise ValueError(f'No combination of unused counts{extra_diff} '
                             f'could be evenly split: ({", ".join(start_counts)})'
                             f'{extra_counts_text}.')

        all_packing_targets: list[PackingTarget|None] = [None] * len(start_packers)
        combined_start_texts = []
        front_shape_block_nums = defaultdict(list)  # {shape: [block_letter]}
        max_width = max(packer.width for packer in start_packers)
        for side_num, side_packers in enumerate(split_packers):
            is_front = side_num == 0
            next_block_num = BlockPacker.GAP + 1
            side_text_lines = []
            for i, packer in enumerate(side_packers):
                if i > 0:
                    side_text_lines.append('#' * max_width)
                source_state = packer.state
                assert source_state is not None
                renumbered_state = source_state.copy()
                for old_block_num, block in packer.create_blocks_with_block_num():
                    if block.shape is None:
                        # Weird block shape will be complained about elsewhere.
                        continue
                    if is_front:
                        shape_name = block.rotated_shape
                        new_block_num = next_block_num
                        next_block_num += 1
                        front_shape_block_nums[shape_name].append(new_block_num)
                    else:
                        front_shape_name = flipped_shapes()[block.rotated_shape]
                        new_block_num = front_shape_block_nums[front_shape_name].pop()
                    renumbered_state[source_state == old_block_num] = new_block_num
                packer_num = start_packers.index(packer)
                all_packing_targets[packer_num] = PackingTarget(
                    packer,
                    is_front,
                    len(side_text_lines))
                packer_lines = packer.display(renumbered_state).splitlines()
                padding = (max_width - packer.width) * '#'
                side_text_lines.extend(line + padding for line in packer_lines)
            combined_start_texts.append('\n'.join(side_text_lines))

        for packing_target in all_packing_targets:
            assert packing_target is not None
            self.packing_targets.append(packing_target)
        return combined_start_texts

    def fill(self) -> bool:
        """ Fill both front and back with the same block shapes and rotations.

        :return: True if no gaps remain, False otherwise.
        """
        self.back_packer.is_logging = self.is_logging
        self.front_packer.is_logging = self.is_logging

        solver = miniexacts_x()

        for prefix, packer in (('b_', self.back_packer),
                               ('f_', self.front_packer)):
            for item_name in packer.find_open_space_items():
                solver.primary(prefix + item_name)

        back_options: dict[str, list[PackingOption]] = defaultdict(list)
        for option in self.back_packer.find_filtered_options():
            back_options[option.rotated_shape_name].append(option)

        flipped_shape_names = flipped_shapes()
        front_masks: dict[int, np.ndarray] = {}
        back_masks: dict[int, np.ndarray] = {}

        front_options = self.front_packer.find_filtered_options()
        if not front_options and not back_options:
            if self.back_packer.unused_count == 0:
                # Unused counts on front and back must match.
                # Already filled.
                return True
        for front_option in front_options:
            back_shape_name = flipped_shape_names[front_option.rotated_shape_name]
            back_shape_options = back_options[back_shape_name]
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

        # solver.write_to_dlx('dump/problem.dlx')
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

    def display_targets(self) -> tuple[str, ...]:
        displays: list[str] = []
        for packing_target in self.packing_targets:
            if packing_target.is_front:
                source_packer = self.front_packer
            else:
                source_packer = self.back_packer
            display = packing_target.display(source_packer)
            displays.append(display)
        return tuple(displays)


@dataclass
class PackingTarget:
    target_packer: XPacker  # Packer for just one grid.
    is_front: bool
    source_line: int = -1  # First related line in combined grid

    def display(self, source_packer: XPacker) -> str:
        target_packer = self.target_packer
        source_line = self.source_line
        height = target_packer.height
        width = target_packer.width
        source_state = source_packer.state
        assert source_state is not None
        state_section = source_state[
            source_line:source_line + height, :width]
        display = self.target_packer.display(state_section)
        return display
