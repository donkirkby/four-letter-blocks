import typing
from dataclasses import dataclass
from random import randrange, choice

from four_letter_blocks.evo import Individual, Evolution
from four_letter_blocks.puzzle import Puzzle


class BlackSet(Individual):
    def __repr__(self):
        return f'BlackSet({self.value!r})'

    def pair(self, other, pair_params):
        return BlackSet(dict(self.value))
    #     scenario = choices(('mother', 'father', 'mix'),
    #                        weights=(5, 5, 1))
    #     if scenario == 'mother':
    #         return Packing(self.value)
    #     if scenario == 'father':
    #         return Packing(other.value)
    #     state1 = self.value['state']
    #     state2 = other.value['state']
    #     grid_size = state1.shape[0]
    #     new_state = np.zeros((grid_size, grid_size), dtype=np.uint8)
    #     counts1 = self.value['shape_counts']
    #     can_rotate = self.value['can_rotate']
    #     mover1 = BlockMover(state1, new_state, can_rotate)
    #     mover1.shape_counts += counts1
    #     mover2 = BlockMover(state2, new_state, can_rotate, mover1.shape_counts)
    #     row1 = randrange(grid_size)
    #     col1 = randrange(grid_size)
    #     row2 = randrange(grid_size)
    #     col2 = randrange(grid_size)
    #
    #     positions1 = ranked_offsets(grid_size) + [row1, col1]
    #     positions2 = ranked_offsets(grid_size) + [row2, col2]
    #     for (i1, j1), (i2, j2) in zip(positions1, positions2):
    #         mover1.move(i1, j1)
    #         mover2.move(i2, j2)
    #     packer = BlockPacker(start_state=new_state)
    #     packer.random_fill(mover1.shape_counts)
    #     return Packing(dict(state=packer.state,
    #                         shape_counts=mover1.shape_counts,
    #                         can_rotate=can_rotate,
    #                         pos1=(row1, col1),
    #                         pos2=(row2, col2)))

    def mutate(self, mutate_params) -> None:
        self.value: dict

        size = self.value['size']
        old_locations = self.value['black_locations']
        new_locations = set(old_locations)
        centre = size // 2
        movable_locations = [(x, y)
                             for x, y in old_locations
                             if x != centre or y != centre]
        x1, y1 = choice(movable_locations)
        x2 = size - 1 - x1
        y2 = size - 1 - y1
        new_locations.discard((x1, y1))
        new_locations.discard((x2, y2))

        while len(new_locations) < len(old_locations):
            x1 = randrange(size)
            y1 = randrange(size)
            x2 = size - 1 - x1
            y2 = size - 1 - y1
            new_locations.add((x1, y1))
            new_locations.add((x2, y2))

        self.value = dict(size=size,
                          black_locations=new_locations)

    def _random_init(self, init_params: dict):
        size = init_params['size']
        black_count = init_params['black_count']
        black_locations = {(size // 2, size // 2)}  # Start with centre black
        while len(black_locations) < black_count:
            x1 = randrange(size)
            y1 = randrange(size)
            x2 = size - 1 - x1
            y2 = size - 1 - y1
            black_locations.add((x1, y1))
            black_locations.add((x2, y2))
        return dict(size=size,
                    black_locations=black_locations)

    def generate_grid_text(self) -> str:
        value = self.value
        size: int = value['size']
        black_locations: set[tuple[int, int]] = value['black_locations']
        grid_lines: list[str] = []
        for y in range(size):
            line = ''.join('#' if (x, y) in black_locations else '.'
                           for x in range(size))
            grid_lines.append(line)
        grid_text = '\n'.join(grid_lines)
        return grid_text


@dataclass(order=True)
class BlackSetFitness:
    score: int  # negative, sum of warning costs


class BlackSetFitnessCalculator:
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

    def calculate(self, black_set: BlackSet) -> BlackSetFitness:
        """ Calculate fitness score based on grid warnings. """
        value = black_set.value
        fitness = value.get('fitness')
        if fitness is not None:
            assert isinstance(fitness, BlackSetFitness)
            return fitness

        grid_text = black_set.generate_grid_text()
        puzzle = Puzzle.parse_sections('', grid_text, '', '')
        warnings = puzzle.score_style()
        fitness = BlackSetFitness(-sum(warning.total_cost
                                       for warning in warnings))

        self.summaries.append(str(fitness))
        value['fitness'] = fitness
        return fitness


class GridGenerator:
    def __init__(self, size: int = 7, black_count: int = 1):
        self.size = size
        self.black_count = black_count
        self.is_logging = False
        self.epochs = 100
        self.current_epoch = 0
        self.evo: Evolution | None = None
        self.top_fitness: BlackSetFitness = BlackSetFitness(-1_000_000)
        self.top_grid: str = ''

    def setup(self,
              fitness_calculator: BlackSetFitnessCalculator | None = None):
        init_params = dict(size=self.size,
                           black_count=self.black_count)
        if fitness_calculator is None:
            fitness_calculator = BlackSetFitnessCalculator()

        self.evo = Evolution(
            pool_size=1000,
            fitness=fitness_calculator.calculate,
            individual_class=BlackSet,
            n_offsprings=200,
            pair_params=None,
            mutate_params=None,
            init_params=init_params,
            pool_count=2)

    def generate(self) -> bool:
        self.setup()
        while self.current_epoch < self.epochs:
            if self.run_epoch():
                return True

        return False

    def run_epoch(self) -> bool:
        """ Run one epoch of the evolutionary search.

        :return: True if a successful packing was found.
        """
        evo = self.evo
        assert evo is not None
        top_individual: BlackSet = evo.pool.individuals[-1]
        top_fitness: BlackSetFitness = evo.pool.fitness(top_individual)
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
                  ', '.join(summaries))
        self.top_fitness = top_fitness
        self.top_grid = top_individual.generate_grid_text()
        if top_fitness.score == 0:
            print('**** Generation successful ****')
            return True

        evo.step()

        new_top_individual = evo.pool.individuals[-1]
        new_top_fitness = evo.pool.fitness(new_top_individual)
        if new_top_fitness.score != top_fitness.score:
            print(new_top_individual.generate_grid_text())

        self.current_epoch += 1
        return False
