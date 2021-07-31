import typing
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType
from itertools import chain

from PySide6.QtGui import QPdfWriter, QPainter, QPageSize
from PySide6.QtWidgets import QApplication

from four_letter_blocks.grid import Grid


def parse_args():
    parser = ArgumentParser(description='Convert a puzzle from text to PDF.',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('source',
                        type=FileType(),
                        help='Text file to convert.')
    parser.add_argument('target',
                        help='PDF file to write.')
    return parser.parse_args()


def draw_grid(grid, painter):
    square_size = painter.window().width() // 30
    for x in range(grid.width):
        for y in range(grid.height):
            square = grid[x, y]
            if square is None:
                continue
            square.resize(square_size)
            square.move_to((x + 1) * square_size,
                           (y + 1) * square_size)
            square.draw(painter)


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


def draw_clues(across_clues, down_clues, painter):
    line_height = painter.window().height() / 40
    centre = painter.window().width() / 2
    painter.drawText(2 * line_height, line_height * 2, 'Across')
    painter.drawText(2 * line_height + centre, line_height * 2, 'Down')
    for number, (word, clue) in enumerate(across_clues.items(), 1):
        painter.drawText(2 * line_height,
                         line_height * (number + 2),
                         f'{number}. {clue}')
    for number, (word, clue) in enumerate(down_clues.items(), 1):
        painter.drawText(2 * line_height + centre,
                         line_height * (number + 2),
                         f'{number}. {clue}')


def main():
    args = parse_args()

    sections = parse_sections(args.source)
    grid = Grid(sections[0])
    across_clues = parse_clues(sections[1], 'across')
    down_clues = parse_clues(sections[2], 'down')

    app = QApplication()
    pdf = QPdfWriter(args.target)
    pdf.setPageSize(QPageSize.Letter)
    painter = QPainter(pdf)

    draw_grid(grid, painter)
    pdf.newPage()
    draw_clues(across_clues, down_clues, painter)
    painter.end()

    print('Done.')
    app.exit()


main()
