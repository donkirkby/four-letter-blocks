from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType

from PySide6.QtGui import QPdfWriter, QPainter, QPageSize
from PySide6.QtWidgets import QApplication

from four_letter_blocks.square import Square


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
    app = QApplication()
    pdf = QPdfWriter(args.target)
    pdf.setPageSize(QPageSize.Letter)
    painter = QPainter(pdf)
    square_size = painter.window().width() // 30
    for y, line in enumerate(args.source):
        line = line.rstrip()
        if not line:
            break
        for x, letter in enumerate(line):
            if letter == '#':
                continue
            square = Square(letter)
            square.resize(square_size)
            if x == 0:
                square.number = y+1
            square.move_to((x + 1)*square_size,
                           (y + 1)*square_size)
            square.draw(painter)
    painter.end()
    print('Done.')
    app.exit()


main()
