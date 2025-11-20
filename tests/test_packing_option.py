import pytest

from four_letter_blocks.block_packer import build_masks
from four_letter_blocks.packing_option import PackingOption


def test_init():
    all_masks = build_masks(5, 5)
    shape_name = 'L0'
    shape_masks = all_masks[shape_name]
    first_mask = shape_masks[0, 0]
    expected_space_items = ['s0_0', 's1_0', 's2_0', 's2_1']

    option = PackingOption(shape_name, first_mask)

    assert option.space_items == expected_space_items


def test_resize_narrower():
    all_masks = build_masks(5, 5)
    shape_name = 'L0'
    shape_masks = all_masks[shape_name]
    first_mask = shape_masks[0, 0]
    option = PackingOption(shape_name, first_mask)

    with pytest.raises(ValueError, match='Cannot resize below width 5.'):
        option.resized(rows=5, cols=4)


def test_resize_shorter():
    all_masks = build_masks(5, 5)
    shape_name = 'L0'
    shape_masks = all_masks[shape_name]
    first_mask = shape_masks[0, 0]
    option = PackingOption(shape_name, first_mask)

    with pytest.raises(ValueError, match='Cannot resize below height 5.'):
        option.resized(rows=4, cols=5)


def test_resize():
    all_masks = build_masks(5, 5)
    shape_name = 'L0'
    shape_masks = all_masks[shape_name]
    first_mask = shape_masks[0, 0]
    option = PackingOption(shape_name, first_mask)
    expected_space_items = ['s2_0', 's3_0', 's4_0', 's4_1']

    option2 = option.resized(rows=7, cols=7)

    assert option2.space_items == expected_space_items