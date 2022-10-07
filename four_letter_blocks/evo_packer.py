import typing
from collections import Counter
from random import randrange

import numpy as np

from four_letter_blocks.evo import Individual, Evolution
from four_letter_blocks.block_packer import BlockPacker


class Packing(Individual):
    def __repr__(self):
        return f'Packing({self.value!r})'

    def pair(self, other, pair_params):
        return Packing(self.value)

    def mutate(self, mutate_params):
        self.value: dict

        state: np.ndarray = self.value['state'].copy()
        shape_counts = Counter(self.value['shape_counts'])
        block_packer = BlockPacker(start_state=state)
        used_blocks = np.unique(state)
        if used_blocks[0] == 0:
            used_blocks = used_blocks[1:]
        if used_blocks[0] == 1:
            used_blocks = used_blocks[1:]
        np.random.shuffle(used_blocks)
        min_removed = min(3, len(used_blocks))
        max_removed = min(10, len(used_blocks))
        remove_count = randrange(min_removed, max_removed+1)

        for block_num in used_blocks[:remove_count]:
            block = block_packer.create_block(block_num)
            shape = block.shape
            shape_counts[shape] += 1
            state[state == block_num] = 0

        block_packer.random_fill(shape_counts)

        self.value = dict(state=block_packer.state, shape_counts=shape_counts)

    def _random_init(self, init_params: dict):
        start_state = init_params['start_state']
        shape_counts = Counter(init_params['shape_counts'])
        block_packer = BlockPacker(start_state=start_state)
        block_packer.random_fill(shape_counts)
        return dict(state=block_packer.state,
                    shape_counts=shape_counts)


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

    def calculate(self, problem):
        """ Calculate fitness score based on the solution.

        -1 for every unused block in shape_counts.
        """
        value = problem.value
        fitness = value.get('fitness')
        if fitness is not None:
            return fitness
        shape_counts: Counter = value['shape_counts']
        fitness = -sum(shape_counts.values())
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
        self.is_logging = True
        self.epochs = 100

    def fill(self, shape_counts: typing.Counter[str]) -> bool:
        init_params = dict(start_state=self.state.copy(),
                           shape_counts=shape_counts)
        fitness_calculator = PackingFitnessCalculator()

        evo = Evolution(
            pool_size=1000,
            fitness=fitness_calculator.calculate,
            individual_class=Packing,
            n_offsprings=200,
            pair_params=None,
            mutate_params=None,
            init_params=init_params,
            pool_count=1)

        hist = []
        for i in range(self.epochs):
            top_individual = evo.pool.individuals[-1]
            top_fitness = evo.pool.fitness(top_individual)
            mid_fitness = evo.pool.fitness(
                evo.pool.individuals[-len(evo.pool.individuals) // 5])
            summaries = []
            for pool in evo.pools:
                pool_fitness = pool.fitness(pool.individuals[-1])
                summaries.append(f'{pool_fitness}')
            if self.is_logging:
                print(i,
                      top_fitness,
                      mid_fitness,
                      repr(top_individual.value['state']),
                      ', '.join(summaries))
            hist.append(top_fitness)
            if top_fitness == 0:
                self.state = top_individual.value['state']
                return True
            evo.step()

        self.state = None
        return False
