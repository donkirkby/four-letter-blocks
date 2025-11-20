from dataclasses import dataclass, field
import typing

import numpy as np


@dataclass
class PackingOption:
    rotated_shape_name: str
    mask: np.ndarray = field(repr=False, hash=False) # 1s in the 4 covered spaces
    space_items: list[str] = field(init=False) # 4 item names

    def __post_init__(self) -> None:
        covered_spaces = [
            (int(i2), int(j2))
            for i2, j2 in zip(*np.where(self.mask))]
        self.space_items = [f's{i2}_{j2}' for i2, j2 in covered_spaces]

    def resized(self, rows: int, cols: int) -> typing.Self:
        old_padded_rows, old_padded_cols = self.mask.shape
        padding = 3
        old_rows = old_padded_rows - padding
        if rows < old_rows:
            raise ValueError(f'Cannot resize below height {old_rows}.')
        old_cols = old_padded_cols - padding
        if cols < old_cols:
            raise ValueError(f'Cannot resize below width {old_cols}.')
        new_mask = np.zeros((rows+padding, cols+padding), self.mask.dtype)
        offset_rows = rows - old_rows
        new_mask[offset_rows:,:old_padded_cols] = self.mask
        return PackingOption(self.rotated_shape_name, new_mask)
