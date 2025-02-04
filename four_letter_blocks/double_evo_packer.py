import typing

import numpy as np

from four_letter_blocks.double_block_packer import DoubleBlockPacker
from four_letter_blocks.evo_packer import (EvoPacker, PackingFitnessCalculator,
                                           FitnessScore)


class DoubleEvoPacker(EvoPacker):
    def __init__(self,
                 front_text: str,
                 back_text: str,
                 tries: int = -1,
                 start_state: np.ndarray | None = None) -> None:
        start_packer = DoubleBlockPacker(front_text,
                                         back_text,
                                         tries,
                                         start_state)
        super().__init__(start_state=start_packer.state[0:start_packer.height],
                         tries=tries)
        self.state = start_packer.state
        self.front_shape_counts = start_packer.front_shape_counts

    def setup(self,
              shape_counts: typing.Counter[str] | None = None,
              fitness_calculator: PackingFitnessCalculator | None = None) -> None:
        if fitness_calculator is None:
            fitness_calculator = DoublePackingFitnessCalculator()
        if shape_counts is None:
            shape_counts = self.front_shape_counts.copy()
        super().setup(shape_counts, fitness_calculator)

    def create_init_params(self, shape_counts):
        init_params = super().create_init_params(shape_counts)
        init_params['packer_class'] = DoubleBlockPacker
        return init_params

    def display(self, state: np.ndarray | None = None) -> str:
        if state is None:
            state = self.state
        packer = DoubleBlockPacker(start_state=state)
        return packer.display()


class DoublePackingFitnessCalculator(PackingFitnessCalculator):
    def calculate_from_state(self, state) -> FitnessScore:
        full_height = state.shape[0]
        height = full_height // 2
        front_state = state[:height]
        back_state = state[height:]
        front_score = super().calculate_from_state(front_state)
        back_score = super().calculate_from_state(back_state)
        front_score.warning_count += back_score.warning_count
        return front_score
