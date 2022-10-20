import random
import typing
from collections import Counter
from dataclasses import dataclass
from functools import cache
from random import randrange

import numpy as np

from four_letter_blocks.evo import Individual, Evolution
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.puzzle import Puzzle


class Packing(Individual):
    def __repr__(self):
        return f'Packing({self.value!r})'

    def pair(self, other, pair_params):
        return Packing(other.value)

    def mutate(self, mutate_params):
        self.value: dict

        state: np.ndarray = self.value['state'].copy()
        shape_counts = Counter(self.value['shape_counts'])
        can_rotate: bool = self.value['can_rotate']
        block_packer = BlockPacker(start_state=state)
        grid_size = state.shape[0]
        gaps = np.argwhere(state == 0)
        if gaps.size > 0:
            row0, col0 = random.choice(gaps)
        else:
            row0 = random.randrange(grid_size)
            col0 = random.randrange(grid_size)
        block_count = (state > 1).sum() // 4
        min_removed = min(3, block_count)
        max_removed = min(10, block_count)
        remove_count = randrange(min_removed, max_removed+1)

        positions = ranked_offsets(grid_size) + [row0, col0]
        for row, col in positions[1:]:
            if not 0 <= row < grid_size:
                continue
            if not 0 <= col < grid_size:
                continue

            block_num = state[row, col]
            if block_num <= 1:
                continue
            block = block_packer.create_block(block_num)
            shape = block.shape
            if not can_rotate:
                shape += str(block.shape_rotation)
            shape_counts[shape] += 1
            state[state == block_num] = 0
            remove_count -= 1
            if remove_count == 0:
                break

        block_packer.random_fill(shape_counts)

        self.value = dict(state=block_packer.state,
                          shape_counts=shape_counts,
                          can_rotate=can_rotate)

    def _random_init(self, init_params: dict):
        start_state = init_params['start_state']
        shape_counts = Counter(init_params['shape_counts'])
        can_rotate = all(len(shape) == 1 for shape in shape_counts)
        block_packer = BlockPacker(start_state=start_state)
        block_packer.random_fill(shape_counts)
        return dict(state=block_packer.state,
                    shape_counts=shape_counts,
                    can_rotate=can_rotate)


@dataclass(order=True)
class FitnessScore:
    empty_spaces: int  # negative
    empty_area: float  # negative, bounding rect of empties as fraction of grid
    warning_count: int = 0  # negative


class PackingFitnessCalculator:
    def __init__(self):
        self.details = []
        self.summaries = []

    def format_summaries(self):
        display = '\n'.join(self.summaries)
        self.summaries.clear()
        return display

    def format_details(self):
        display = '\n\n'.join(self.details)
        self.details.clear()
        return display

    def calculate(self, packing):
        """ Calculate fitness score based on the solution.

        -1 for every unused block in shape_counts.
        """
        value = packing.value
        fitness = value.get('fitness')
        if fitness is not None:
            return fitness
        state = value['state']
        empty = np.nonzero(state == 0)
        empty_spaces = empty[0].size

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
                               warning_count=-warning_count)
        self.summaries.append(str(fitness))

        value['fitness'] = fitness
        return fitness


class EvoPacker(BlockPacker):
    def __init__(self,
                 width=0,
                 height=0,
                 tries=-1,
                 min_tries=-1,
                 start_text: str = None,
                 start_state: np.ndarray = None):
        super().__init__(width,
                         height,
                         tries,
                         min_tries,
                         start_text,
                         start_state)
        self.is_logging = False
        self.epochs = 100
        self.current_epoch = 0
        self.shape_counts: typing.Counter[str] = Counter()
        self.evo: Evolution | None = None
        self.top_fitness: FitnessScore = FitnessScore(0, 0)
        self.top_blocks = ''

    def setup(self, shape_counts: typing.Counter[str]):
        init_params = dict(start_state=self.state.copy(),
                           shape_counts=shape_counts)
        fitness_calculator = PackingFitnessCalculator()

        self.evo = Evolution(
            pool_size=1000,
            fitness=fitness_calculator.calculate,
            individual_class=Packing,
            n_offsprings=200,
            pair_params=None,
            mutate_params=None,
            init_params=init_params,
            pool_count=2)
        self.shape_counts = shape_counts

    def fill(self, shape_counts: typing.Counter[str]) -> bool:
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
        top_individual = evo.pool.individuals[-1]
        top_fitness: FitnessScore = evo.pool.fitness(top_individual)
        mid_fitness = evo.pool.fitness(
            evo.pool.individuals[-len(evo.pool.individuals) // 5])
        summaries = []
        for pool in evo.pools:
            pool_fitness = pool.fitness(pool.individuals[-1])
            summaries.append(f'{pool_fitness}')
        if self.is_logging:
            print(self.current_epoch,
                  top_fitness,
                  mid_fitness,
                  repr(top_individual.value['state']),
                  ', '.join(summaries))
        if top_fitness.empty_spaces == 0 and top_fitness.warning_count == 0:
            self.state = top_individual.value['state']
            return True
        self.top_fitness = top_fitness
        packer = BlockPacker(start_state=top_individual.value['state'])
        packer.sort_blocks()
        self.top_blocks = packer.display()
        evo.step()
        self.current_epoch += 1
        return False

    def find_usable_packing(self) -> bool:
        evo = self.evo
        top_individual = evo.pool.individuals[-1]
        top_fitness: FitnessScore = evo.pool.fitness(top_individual)
        if top_fitness is not None and top_fitness.empty_spaces == 0:
            self.state = top_individual.value['state']
            return True
        self.state = None
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
    position_pairs = np.column_stack(divmod(positions, expanded_size))
    position_pairs -= [grid_size-1, grid_size-1]
    position_pairs.setflags(write=False)
    return position_pairs.view()
