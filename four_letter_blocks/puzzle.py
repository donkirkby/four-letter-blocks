import typing
from dataclasses import dataclass
from itertools import chain

from four_letter_blocks.grid import Grid


@dataclass
class Puzzle:
    grid: Grid
    across_clues: typing.Dict[str, str]
    down_clues: typing.Dict[str, str]

    @staticmethod
    def parse(source_file: typing.IO) -> 'Puzzle':
        sections = parse_sections(source_file)
        puzzle = Puzzle(Grid(sections[0]),
                        parse_clues(sections[1], 'across'),
                        parse_clues(sections[2], 'down'))
        return puzzle


def parse_sections(source_file):
    sections: typing.List[str] = []
    lines: typing.List[str] = []
    for line in chain(source_file, '\n'):
        line = line.rstrip()
        if line:
            lines.append(line)
        else:
            section = '\n'.join(lines)
            if section:
                sections.append(section)
            lines.clear()
    section_count = len(sections)
    if section_count != 4:
        exit(f'Expected 4 sections, found {section_count}.')
    return sections


def parse_clues(text, label):
    clues: typing.Dict[str, str] = {}
    pairs = text.splitlines(keepends=False)
    if pairs[0].lower() == label:
        pairs.pop(0)
    for pair in pairs:
        word, clue = pair.split('-', maxsplit=1)
        word = word.strip()
        clues[word] = clue.strip()
    return clues
