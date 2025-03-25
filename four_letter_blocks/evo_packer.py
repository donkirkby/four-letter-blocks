import re
import typing
from collections import Counter
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime
from functools import cache
from itertools import count
from random import randrange, choices, choice

import numpy as np

from four_letter_blocks.evo import Individual, Evolution
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.puzzle import Puzzle


class BlockMover:
    def __init__(self,
                 source: np.ndarray,
                 target: np.ndarray,
                 can_rotate: bool,
                 shape_counts: typing.Counter[str | None] | None = None):
        self.source = source
        self.target = target
        self.can_rotate = can_rotate
        self.packer = BlockPacker(start_state=self.source)
        self.blocks = {
            block_number: block
            for block_number, block in self.packer.create_blocks_with_block_num()}
        if shape_counts is not None:
            self.shape_counts = shape_counts
        else:
            self.shape_counts = Counter()
            for block in self.blocks.values():
                shape = block.shape
                if shape != 'O' and shape is not None and not can_rotate:
                    shape += str(block.shape_rotation)
                self.shape_counts[shape] += 1

    def move(self, row: int, col: int):
        grid_size = self.source.shape[0]
        if not 0 <= row < grid_size:
            return
        if not 0 <= col < grid_size:
            return
        # noinspection PyTypeChecker
        block_num: int = self.source[row, col]
        if block_num == 1:
            self.target[row, col] = 1
            return
        try:
            block = self.blocks.pop(block_num)
        except KeyError:
            return
        shape = block.shape
        assert shape is not None
        if shape != 'O' and not self.can_rotate:
            shape += str(block.shape_rotation)
        if self.shape_counts[shape] == 0:
            return
        for square in block.squares:
            if self.target[square.y, square.x] != 0:
                return
        # noinspection PyUnresolvedReferences
        if (self.target == block_num).any():
            used_nums = set(np.unique(self.target))
            for block_num in count(2):
                if block_num not in used_nums:
                    break
        for square in block.squares:
            self.target[square.y, square.x] = block_num
        self.shape_counts[shape] -= 1


class Packing(Individual):
    """ Represents one individual in an evolutionary population of packings.

    init_params control the packing, see _random_init() for details.
    self.value records the state and controls the packing, see the return value
    of _random_init() for details.
    """
    def __repr__(self):
        return f'Packing({self.value!r})'

    def pair(self, other, pair_params):
        scenario = choices(('mother', 'father', 'mix'),
                           weights=(5, 5, 1*0))[0]
        if scenario == 'mother':
            return Packing(self.value)
        if scenario == 'father':
            return Packing(other.value)
        state1 = self.value['state']
        state2 = other.value['state']
        grid_size = state1.shape[0]
        new_state = np.zeros((grid_size, grid_size), dtype=np.uint8)
        counts1 = self.value['shape_counts']
        can_rotate = self.value['can_rotate']
        mover1 = BlockMover(state1, new_state, can_rotate)
        mover1.shape_counts += counts1
        mover2 = BlockMover(state2, new_state, can_rotate, mover1.shape_counts)
        row1 = randrange(grid_size)
        col1 = randrange(grid_size)
        row2 = randrange(grid_size)
        col2 = randrange(grid_size)

        positions1 = ranked_offsets(grid_size) + [row1, col1]
        positions2 = ranked_offsets(grid_size) + [row2, col2]
        for (i1, j1), (i2, j2) in zip(positions1, positions2):
            mover1.move(i1, j1)
            mover2.move(i2, j2)
        packer_class = self.value['packer_class']
        tries = self.value['tries']
        packer = packer_class(start_state=new_state, tries=tries)
        packer.force_fours = self.value['force_fours']
        packer.are_slots_shuffled = True
        packer.are_partials_saved = True
        packer.fill(mover1.shape_counts)

        assert packer.state is not None
        return Packing(dict(state=packer.state,
                            shape_counts=mover1.shape_counts,
                            can_rotate=can_rotate,
                            pos1=(row1, col1),
                            pos2=(row2, col2),
                            packer_class=packer_class,
                            force_fours=packer.force_fours,
                            tries=tries))

    def mutate(self, mutate_params) -> None:
        self.value: dict

        state: np.ndarray | tuple = deepcopy(self.value['state'])
        shape_counts = Counter(self.value['shape_counts'])
        can_rotate: bool = self.value['can_rotate']
        packer_class = self.value['packer_class']
        tries = self.value['tries']
        block_packer: BlockPacker = packer_class(start_state=state,
                                                 tries=tries)
        block_packer.force_fours = self.value['force_fours']
        block_packer.are_partials_saved = True
        block_packer.are_slots_shuffled = True
        start_state = block_packer.state
        grid_size = max(block_packer.width, block_packer.height)
        gaps = np.argwhere(start_state == 0)
        if gaps.size > 0:
            row0, col0 = choice(gaps)
        else:
            display = block_packer.display()
            puzzle = Puzzle.parse_sections('',
                                           display,
                                           '',
                                           display)
            targets = []
            for warning in puzzle.check_word_length():
                match = re.match(r'complete.*from \((\d+), (\d+)\) '
                                 r'to \((\d+), (\d+)\)',
                                 warning)
                if match:
                    start_col = int(match.group(1))
                    start_row = int(match.group(2))
                    end_col = int(match.group(3))
                    end_row = int(match.group(4))
                    for col in range(start_col, end_col+1):
                        for row in range(start_row, end_row+1):
                            targets.append((col-1, row-1))
            if targets:
                col0, row0 = choice(targets)
            else:
                row0 = randrange(block_packer.height)
                col0 = randrange(block_packer.width)
        block_count = (start_state > 1).sum() // 4  # type: ignore
        min_removed = 0  # min(3, block_count)
        max_removed = min(10, block_count)
        remove_count = randrange(min_removed, max_removed+1)

        positions = ranked_offsets(grid_size) + [row0, col0]
        for row, col in positions[1:]:
            if not 0 <= row < block_packer.height:
                continue
            if not 0 <= col < block_packer.width:
                continue

            try:
                shape = block_packer.remove_block(row, col)
            except ValueError:
                continue

            shape_counts[shape] += 1
            remove_count -= 1
            if remove_count == 0:
                break

        block_packer.fill(shape_counts)

        assert block_packer.state is not None
        self.value = dict(state=block_packer.state,
                          shape_counts=shape_counts,
                          can_rotate=can_rotate,
                          packer_class=packer_class,
                          force_fours=block_packer.force_fours,
                          tries=tries)

    def _random_init(self, init_params: dict):
        start_state = init_params['start_state']
        shape_counts = Counter(init_params['shape_counts'])
        can_rotate = all(len(shape) == 1 for shape in shape_counts)
        packer_class = init_params.get('packer_class', BlockPacker)
        tries = init_params['tries']
        block_packer = packer_class(start_state=start_state,
                                    tries=tries)
        block_packer.force_fours = init_params.get('force_fours', False)
        block_packer.are_slots_shuffled = True
        block_packer.are_partials_saved = True
        block_packer.fill(shape_counts)

        assert block_packer.state is not None
        return dict(state=block_packer.state,
                    shape_counts=shape_counts,
                    can_rotate=can_rotate,
                    force_fours=block_packer.force_fours,
                    packer_class=packer_class,
                    tries=tries)


@dataclass(order=True)
class FitnessScore:
    empty_spaces: int  # negative
    empty_area: float  # negative, bounding rect of empties as fraction of grid
    missed_targets: int = 0  # negative
    warning_count: int = 0  # negative


class PackingFitnessCalculator:
    def __init__(self) -> None:
        self.details: typing.List[str] = []
        self.summaries: typing.List[str] = []
        self.count_parities: typing.Dict[str, int] = {}
        self.count_diffs: typing.Dict[str, int] = {}  # {ab: diff}
        self.count_min: typing.Dict[str, int] = {}  # {shapes: min}
        self.count_max: typing.Dict[str, int] = {}  # {shapes: max}

    def format_summaries(self):
        display = '\n'.join(self.summaries)
        self.summaries.clear()
        return display

    def format_details(self):
        display = '\n\n'.join(self.details)
        self.details.clear()
        return display

    def calculate(self, packing: Packing) -> FitnessScore:
        """ Calculate fitness score based on the solution. """
        value = packing.value
        fitness_x: FitnessScore | None = value.get('fitness')
        if fitness_x is not None:
            return fitness_x
        state = value['state']
        fitness = self.calculate_from_state(state)
        self.summaries.append(str(fitness))

        value['fitness'] = fitness
        return fitness

    def calculate_from_state(self, state) -> FitnessScore:
        # noinspection PyTypeChecker
        empty = np.nonzero(state == 0)
        empty_spaces = empty[0].size
        missed_targets = 0

        if empty_spaces == 0:
            empty_fraction = 0
            packer = BlockPacker(start_state=state)
            display = packer.display()
            puzzle = Puzzle.parse_sections('',
                                           display,
                                           '',
                                           display)
            warning_count = sum(1
                                for warning in puzzle.check_word_length()
                                if warning.startswith('complete word'))
            # Required features to balance the puzzle set.
            shape_counts = puzzle.shape_counts
            for shape, parity in self.count_parities.items():
                if shape_counts[shape] % 2 != parity:
                    missed_targets += 1
            for shapes, expected_diff in self.count_diffs.items():
                assert len(shapes) == 2
                shape1 = shapes[0]
                shape2 = shapes[1]
                actual_diff = shape_counts[shape1] - shape_counts[shape2]
                missed_targets += abs(actual_diff)
            for shapes, expected_min in self.count_min.items():
                actual_count = sum(shape_counts[shape] for shape in shapes)
                if actual_count < expected_min:
                    missed_targets += expected_min - actual_count
            for shapes, expected_max in self.count_max.items():
                actual_count = sum(shape_counts[shape] for shape in shapes)
                if actual_count > expected_max:
                    missed_targets += actual_count - expected_max
        else:
            warning_count = 0
            min_row = min(empty[0])
            max_row = max(empty[0])
            min_col = min(empty[1])
            max_col = max(empty[1])
            total_area = state.shape[0] * state.shape[1]
            empty_area = (max_row-min_row+1) * (max_col-min_col+1)
            empty_fraction = round(empty_area / total_area, 3)
        fitness = FitnessScore(empty_spaces=-empty_spaces,
                               empty_area=-empty_fraction,
                               missed_targets=-missed_targets,
                               warning_count=-warning_count)
        self.summaries.append(str(fitness))
        return fitness


class EvoPacker(BlockPacker):
    def __init__(self,
                 width=0,
                 height=0,
                 tries=-1,
                 min_tries=-1,
                 start_text: str | None = None,
                 start_state: np.ndarray | None = None):
        super().__init__(width,
                         height,
                         tries,
                         min_tries,
                         start_text,
                         start_state)
        self.is_logging = False
        self.epochs = 100
        self.pool_size = 1000
        self.current_epoch = 0
        self.shape_counts: typing.Counter[str] = Counter()
        self.evo: Evolution | None = None
        self.top_fitness: FitnessScore = FitnessScore(
            -self.width * self.height,
            0)
        self.top_blocks = ''
        self.top_choices: set[str] = set()

    def setup(self,
              shape_counts: typing.Counter[str],
              fitness_calculator: PackingFitnessCalculator | None = None):
        assert self.state is not None
        init_params = self.create_init_params(shape_counts)
        if fitness_calculator is None:
            fitness_calculator = PackingFitnessCalculator()
        fitness_calculator.summaries.clear()

        self.evo = Evolution(
            pool_size=self.pool_size,
            fitness=fitness_calculator.calculate,
            individual_class=Packing,
            n_offsprings=self.pool_size // 5,
            pair_params=None,
            mutate_params=None,
            init_params=init_params,
            pool_count=2)
        self.shape_counts = shape_counts

    def create_init_params(self, shape_counts):
        init_params = dict(start_state=self.state.copy(),
                           shape_counts=shape_counts,
                           tries=self.tries,
                           force_fours=self.force_fours)
        return init_params

    def fill(self, shape_counts: typing.Counter[str] | None = None) -> bool:
        if shape_counts is None:
            shape_counts = self.calculate_max_shape_counts()
        self.setup(shape_counts)
        while self.current_epoch < self.epochs:
            if self.run_epoch():
                return True

        return self.find_usable_packing()

    def run_epoch(self) -> bool:
        """ Run one epoch of the evolutionary search.

        :return: True if a successful packing was found.
        """
        evo = self.evo
        assert evo is not None
        top_individual = evo.pool.individuals[-1]
        top_fitness: FitnessScore = evo.pool.fitness(top_individual)
        mid_fitness = evo.pool.fitness(
            evo.pool.individuals[-len(evo.pool.individuals) // 5])
        summaries = []
        for pool in evo.pools:
            pool_fitness = pool.fitness(pool.individuals[-1])
            summaries.append(f'{pool_fitness}')
        if self.is_logging:
            print(datetime.now().strftime('%H:%M'),
                  self.current_epoch,
                  top_fitness,
                  mid_fitness,
                  ', '.join(summaries))
        if top_fitness >= self.top_fitness:
            packer_class = top_individual.value['packer_class']
            packer = packer_class(start_state=top_individual.value['state'],
                                  tries=top_individual.value['tries'])
            packer.force_fours = True
            packer.sort_blocks()
            packer_display = packer.display()
            if top_fitness > self.top_fitness:
                self.top_fitness = top_fitness
                self.top_choices.clear()
                self.top_blocks = packer_display
            if packer_display not in self.top_choices:
                self.top_choices.add(packer_display)
                if self.is_logging:
                    print(f'Packing {len(self.top_choices)}:')
                    print(packer_display)
        if (top_fitness.empty_spaces == 0 and
                top_fitness.missed_targets == 0 and
                top_fitness.warning_count == 0):
            self.state = top_individual.value['state']
            return True
        evo.step()
        self.current_epoch += 1
        return False

    def find_usable_packing(self) -> bool:
        evo = self.evo
        assert evo is not None
        original_state = self.state
        top_individual = evo.pool.individuals[-1]
        top_fitness: FitnessScore = evo.pool.fitness(top_individual)
        if top_fitness is not None and top_fitness.empty_spaces == 0:
            self.state = top_individual.value['state']
            return True
        self.state = original_state
        return False


@cache
def distance_ranking(grid_size: int) -> np.ndarray:
    """ Rank the positions in a grid by their distance from the centre.

    :param grid_size: the size of the square grid
    :return: an array with 0 at the centre and increasing numbers as they move
    out. Ties are broken by the angle counterclockwise from the x-axis.
    """
    x0 = y0 = grid_size // 2
    x = np.arange(grid_size)
    y = np.arange(grid_size)
    xs, ys = np.meshgrid(x, y, sparse=True)
    xs -= x0
    ys = y0 - ys
    distances = np.sqrt(xs*xs + ys*ys).round()
    angles = np.mod(np.arctan2(ys, xs), 2*np.pi) / (2*np.pi)
    scores = distances + angles
    indexes = scores.argsort(axis=None)
    ranks = indexes.argsort(axis=None).reshape(grid_size, grid_size)
    ranks.setflags(write=False)
    return ranks.view()


@cache
def ranked_offsets(grid_size: int) -> np.ndarray:
    """ List the offsets of a grid position in ranked order by distance.

    :param grid_size: the size of the square grid
    :return: an array of [d_row, d_column] entries for the positions, in order
    of distance from the starting point. Ties are broken by the angle
    counterclockwise from the x-axis. Positions go in all directions, so the
    final grid is almost twice as big.
    """
    expanded_size = grid_size * 2 - 1
    rankings = distance_ranking(expanded_size)
    positions = rankings.argsort(axis=None)
    # noinspection PyTypeChecker
    position_pairs = np.column_stack(divmod(positions, expanded_size))
    position_pairs -= [grid_size-1, grid_size-1]
    position_pairs.setflags(write=False)
    return position_pairs.view()
