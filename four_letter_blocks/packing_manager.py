from dataclasses import dataclass
from enum import StrEnum, auto
from multiprocessing.queues import Queue

from four_letter_blocks.double_block_packer import DoubleBlockPacker
from four_letter_blocks.x_packer import XPacker


class PackingScenario(StrEnum):
    # Pack one puzzle's grid. inputs: target_texts[0] (black squares, unpacked)
    SINGLE_PUZZLE = auto()
    # Pack front and back puzzles with flipped shape counts. inputs:
    #    target_texts (black squares, unpacked)
    PUZZLE_PAIR = auto()
    # Pack front and back puzzles with flipped shape counts. inputs:
    #    target_texts (black squares, unpacked)
    PUZZLE_SET = auto()

    # Are travel packings fast enough for main thread?
    # Pack a travel grid with the shape counts from a puzzle. inputs:
    #    target_texts[0] (no black squares, unpacked),
    #    source_texts[0] (black squares, packed)
    TRAVEL_PUZZLE = auto()
    # Pack a travel grid with the shape counts from multiple puzzles. inputs:
    #    target_texts[0] (no black squares, unpacked),
    #    source_texts (black squares, packed)
    TRAVEL_SET = auto()


@dataclass(frozen=True)
class PackingRequest:
    scenario: PackingScenario
    target_texts: tuple[str, ...]
    source_texts: tuple[str, ...] = ()  # Only needed for travel scenarios

@dataclass(frozen=True)
class PackingResponse:
    scenario: PackingScenario
    target_texts: tuple[str, ...] = ()
    source_texts: tuple[str, ...] = ()
    sides: tuple[tuple[int, ...], tuple[int, ...]] = ((), ())  # target_texts indexes


class PackingManager:
    def __init__(self, packing_request: PackingRequest, queue: Queue):
        self.packing_request = packing_request
        self.queue = queue

    def pack(self):
        request = self.packing_request
        if request.scenario == PackingScenario.SINGLE_PUZZLE:
            packer = XPacker(start_text=request.target_texts[0])
            is_filled = packer.fill()
            if is_filled:
                target_texts = (packer.display(),)
            else:
                target_texts = ()
            response = PackingResponse(scenario=request.scenario,
                                       target_texts=target_texts)
        else:
            packer = DoubleBlockPacker(*request.target_texts)
            packer.is_logging = True
            is_filled = packer.fill()
            response = None
        self.queue.put(response)
