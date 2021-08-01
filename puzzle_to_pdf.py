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


def main():
    args = parse_args()
    puzzle = Puzzle.parse(args.source)

    app = QApplication()
    pdf = QPdfWriter(args.target)
    pdf.setPageSize(QPageSize.Letter)
    painter = QPainter(pdf)

    puzzle.draw_pieces(painter)
    pdf.newPage()
    puzzle.draw_clues(painter)
    painter.end()

    print('Done.')
    app.exit()


main()
