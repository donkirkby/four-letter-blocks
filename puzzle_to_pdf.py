from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType

from PySide6.QtGui import QPdfWriter, QPageSize, QPainter
from PySide6.QtWidgets import QApplication

from four_letter_blocks.puzzle import Puzzle


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
    puzzle = Puzzle.parse(args.source)

    app = QApplication()
    pdf = QPdfWriter(args.target)
    pdf.setPageSize(QPageSize.Letter)
    painter = QPainter(pdf)

    draw_grid(puzzle.grid, painter)
    pdf.newPage()
    draw_clues(puzzle.across_clues, puzzle.down_clues, painter)
    painter.end()

    print('Done.')
    app.exit()


main()
