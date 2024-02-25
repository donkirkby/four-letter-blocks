import math
import typing
from collections import Counter, defaultdict
from collections.abc import Iterable

from PySide6.QtCore import QPoint
from PySide6.QtGui import QPainter, QColor, QPixmap, QPainterPath, \
    QBrush, QLinearGradient
from colorspacious import cspace_convert  # type:ignore[import]

from four_letter_blocks.block import Block
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.puzzle import Puzzle, draw_rotated_tiles, RotationsDisplay


class PuzzleSet:
    LINK_TEXT = 'https://donkirkby.github.io/four-letter-blocks'

    def __init__(self,
                 *puzzles: Puzzle,
                 block_packer: BlockPacker | None = None,
                 start_hue: int = 0):
        self.puzzles = puzzles
        self.shape_counts: typing.Counter[str] = Counter()
        if block_packer:
            self.block_packer = block_packer
        else:
            self.block_packer = BlockPacker(16, 20,  # Game Crafter cutout size
                                            tries=10_000)
        self.front_blocks: typing.Dict[
            str,
            typing.List[Block | None]] = defaultdict(list)
        self.back_blocks: typing.Dict[
            str,
            typing.List[Block | None]] = defaultdict(list)

        self.block_summary = ''
        self.combos = {'J': 'JL', 'L': 'JL', 'S': 'SZ', 'Z': 'SZ'}
        self.pairs = {}
        for pair in self.combos.values():
            first: str
            last: str
            first, last = pair  # type:ignore[misc]
            self.pairs[first] = last
            self.pairs[last] = first
        self.start_hue = start_hue
        self.count_parities: typing.Dict[str, int] = {}
        self.count_diffs: typing.Dict[str, int] = {}
        self.count_min: typing.Dict[str, int] = {}
        self.count_max: typing.Dict[str, int] = {}
        self.pack_puzzles()

    def pack_puzzles(self):
        for i, puzzle in enumerate(self.puzzles):
            puzzle.rotations_display = RotationsDisplay.FRONT
        combos = self.combos
        pairs = self.pairs
        total_counts = Counter()
        total_block_count = 0
        max_counts = Counter()
        max_puzzles = {}  # {combo: index}
        source_puzzles = defaultdict(list)  # {combo: [index]}
        for i, puzzle in enumerate(self.puzzles):
            puzzle_counts = Counter()
            for label, count in puzzle.shape_counts.items():
                total_block_count += count
                combo = combos.get(label, label)
                puzzle_counts[combo] += count
                if combo != label:
                    puzzle_counts[label] += count
            total_counts += puzzle_counts
            for combo, count in puzzle_counts.items():
                source_puzzles[combo].append(i)
                if count > max_counts[combo]:
                    max_counts[combo] = count
                    max_puzzles[combo] = i
        all_combos = set(Block.shape_names())
        all_combos.update(combos.values())
        extras = []
        for combo in sorted(all_combos):
            total_count = total_counts[combo]
            max_count = max_counts[combo]
            mirror = pairs.get(combo)
            if mirror is None:
                extra = 2 * max_count - total_count
                self.count_parities[combo] = total_count % 2
                self.count_min[combo] = extra
                self.count_max[combo] = total_count
                if extra > 0:
                    extras.append(f'{combo}: {extra}({max_puzzles[combo] + 1})')
                elif total_count % 2 != 0:
                    extras.append(f'{combo}: 1')
                if len(combo) == 1:
                    self.shape_counts[combo] = max(math.ceil(total_count / 2),
                                                   max_count)
            else:
                full_combo = combos[combo]
                max_count = max_counts[full_combo]
                mirror_count = total_counts[mirror]
                extra = total_count - mirror_count
                if extra > 0:
                    extras.append(f'{combo}: {extra}')
                if combo < mirror:
                    self.shape_counts[combo] = max(total_count,
                                                   mirror_count,
                                                   max_count)
                    self.count_diffs[full_combo] = -extra

        for combo in all_combos:
            if len(combo) > 1:
                continue
            total_count = total_counts[combo]
            front_shape = combo
            back_shape = pairs.get(front_shape, front_shape)
            if front_shape == back_shape:
                front_count = math.ceil(total_count / 2)
                back_count = total_count - front_count
                max_count = max_counts[front_shape]
            elif front_shape > back_shape:
                continue
            else:
                front_count = total_count
                back_count = total_counts[back_shape]
                max_count = max_counts[front_shape + back_shape]
            block_count = max(front_count, back_count, max_count)
            front_shape_blocks = [None] * block_count
            back_shape_blocks = [None] * block_count
            self.front_blocks[front_shape] = front_shape_blocks
            self.back_blocks[back_shape] = back_shape_blocks
            puzzle_counts = [(len(puzzle.shape_blocks[front_shape]) +
                              len(puzzle.shape_blocks[back_shape]),
                              i)
                             for i, puzzle in enumerate(self.puzzles)]
            puzzle_counts.sort(reverse=True)
            is_top = False
            for _, puzzle_index in puzzle_counts:
                is_top = not is_top
                puzzle = self.puzzles[puzzle_index]
                front_source = puzzle.shape_blocks[front_shape]
                if front_shape == back_shape:
                    back_source = front_source
                else:
                    back_source = puzzle.shape_blocks[back_shape]
                targets = list(range(block_count))
                if is_top:
                    targets.reverse()
                while targets:
                    front_room = sum(1
                                     for target in targets
                                     if front_shape_blocks[target] is None)
                    back_room = sum(1
                                    for target in targets
                                    if back_shape_blocks[target] is None)
                    front_extra = front_room - len(front_source)
                    back_extra = back_room - len(back_source)
                    target = targets.pop()
                    front = front_shape_blocks[target]
                    back = back_shape_blocks[target]
                    side = None
                    if front is not None:
                        if back is None:
                            side = 'B'
                    elif back is not None:
                        side = 'F'
                    elif front_source and front_extra == 0:
                        side = 'F'
                    elif back_source and back_extra == 0:
                        side = 'B'
                    elif len(front_source) >= len(back_source):
                        side = 'F'
                    else:
                        side = 'B'
                    if side == 'F' and front_source:
                        front_shape_blocks[target] = front_source.pop()
                    elif side == 'B' and back_source:
                        back_shape_blocks[target] = back_source.pop()
                if front_source or back_source:
                    raise RuntimeError("Blocks wouldn't fit.")

        self.block_summary = f'{total_block_count} blocks'
        if extras:
            self.block_summary += ' with extras: ' + ', '.join(extras)
        is_filled = self.block_packer.fill(self.shape_counts)
        if not is_filled:
            raise RuntimeError("Blocks wouldn't fit.")
        self.set_face_colours()

    def set_face_colours(self):
        if not self.puzzles:
            return

        size_pairs = [(puzzle.grid.width, i)
                      for i, puzzle in enumerate(self.puzzles)]
        size_pairs.sort()
        angle = 360 / len(self.puzzles)
        for i, (width, puzzle_index) in enumerate(size_pairs):
            puzzle = self.puzzles[puzzle_index]
            lightness = 77
            chroma = 20
            hue = (self.start_hue + i * angle) % 360
            rgb = cspace_convert((lightness, chroma, hue), "JCh", "sRGB255")
            colour = QColor.fromRgb(*rgb)
            puzzle.face_colour = colour

    @property
    def square_size(self) -> int:
        return self.puzzles[0].square_size

    @square_size.setter
    def square_size(self, square_size: int):
        for puzzle in self.puzzles:
            puzzle.square_size = square_size

    @property
    def tab_count(self) -> int:
        return self.puzzles[0].blocks[0].tab_count

    @tab_count.setter
    def tab_count(self, tab_count: int):
        for puzzle in self.puzzles:
            for block in puzzle.blocks:
                block.tab_count = tab_count

    def display_blocks(
            self,
            block_packer: BlockPacker,
            blocks: typing.Dict[str, typing.List[Block | None]]) -> Iterable[Block]:
        square_size = self.square_size
        can_rotate = all(len(shape) == 1 for shape in blocks)
        if can_rotate:
            positions = block_packer.positions
        else:
            positions = block_packer.rotated_positions
        for shape, shape_blocks in blocks.items():
            shape_positions = positions[shape][:]
            for block in shape_blocks:
                if can_rotate:
                    x, y, rotation = shape_positions.pop()
                else:
                    x, y = shape_positions.pop()
                    if shape == 'O':
                        rotation = 0
                    else:
                        rotation = int(shape[1])
                if block is None:
                    continue
                block.set_display((x+0.5)*square_size,
                                  (y+0.5)*square_size,
                                  rotation)
                yield block

    def draw_cuts(self, painter, nick_radius=0):
        square_size = self.square_size
        tab_count = self.tab_count
        blocks = self.block_packer.create_blocks()
        for block in blocks:
            block.tab_count = tab_count
            for square in block.squares:
                square.size = square_size
                square.x = (square.x + 0.5) * square_size
                square.y = (square.y + 0.5) * square_size
            block.border_colour = Block.CUT_COLOUR
            if self.can_draw_block(block):
                block.draw_outline(painter, nick_radius)

    def draw_front(self, painter: QPainter):
        for block in self.display_blocks(self.block_packer,
                                         self.front_blocks):
            if self.can_draw_block(block):
                block.draw(painter, is_packed=True)

    # noinspection PyUnusedLocal,PyMethodMayBeStatic
    def can_draw_block(self, block: Block) -> bool:
        return True

    def draw_back(self, painter: QPainter):
        block_packer = self.block_packer.flip()
        for block in self.display_blocks(block_packer, self.back_blocks):
            if self.can_draw_block(block):
                block.draw(painter, is_packed=True)

    @staticmethod
    def draw_background(painter: QPainter, tile: QPixmap):
        for y in range(0, painter.window().height(), tile.height()):
            for x in range(0, painter.window().width(), tile.width()):
                painter.drawPixmap(x, y, tile)

    def draw_background_tile(self, painter) -> None:
        background: QColor = painter.background().color()
        dark, light = self.get_target_colours(background, shift=4)
        window = painter.window()
        size = window.width()
        for i in range(2):
            for j in range(2):
                if i % 2 == j % 2:
                    target_colour = light
                else:
                    target_colour = dark
                painter.translate(j*size/2, i*size/2)
                gradient = QLinearGradient(0, 0, 0, size/4)
                gradient.setStops(((0, background), (1, target_colour)))
                gradient.setSpread(gradient.Spread.ReflectSpread)
                for y in (0, size/2):
                    path = QPainterPath(QPoint(0, y))
                    path.lineTo(size/4, size/4)
                    path.lineTo(size/2, y)
                    path.lineTo(0, y)
                    painter.fillPath(path, QBrush(gradient))
                gradient = QLinearGradient(0, 0, size/4, 0)
                gradient.setStops(((0, background), (1, target_colour)))
                gradient.setSpread(gradient.Spread.ReflectSpread)
                for x in (0, size/2):
                    path = QPainterPath(QPoint(x, 0))
                    path.lineTo(size/4, size/4)
                    path.lineTo(x, size/2)
                    path.lineTo(x, 0)
                    painter.fillPath(path, QBrush(gradient))
                painter.translate(-j*size/2, -i*size/2)

    @staticmethod
    def get_target_colours(start, shift):
        rgb = start.toRgb().toTuple()[:3]
        lightness, chroma, hue = cspace_convert(rgb, 'sRGB255', 'JCh')
        light_jch = [lightness+shift, chroma, hue]
        dark_jch = [lightness-shift, chroma, hue]
        light_rgb = cspace_convert(light_jch, 'JCh', 'sRGB255')
        dark_rgb = cspace_convert(dark_jch, 'JCh', 'sRGB255')
        light = QColor.fromRgb(*light_rgb)
        dark = QColor.fromRgb(*dark_rgb)
        return dark, light

    def draw_background_pattern(self,
                                painter: QPainter,
                                size: float,
                                x_offset: int = 0,
                                y_offset: int = 0):
        tile = self.create_background_tile(round(size),
                                           painter.background().color())
        draw_rotated_tiles(tile, painter, size, x_offset, y_offset)

    def create_background_tile(self, tile_size: int,
                               background: QColor) -> QPixmap:
        tile = QPixmap(tile_size, tile_size)
        tile_painter = QPainter(tile)
        tile_painter.setBackground(background)
        tile_painter.eraseRect(tile_painter.window())
        try:
            self.draw_background_tile(tile_painter)
        finally:
            tile_painter.end()
        return tile
