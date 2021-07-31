from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, FileType
from pathlib import Path

from bs4 import BeautifulSoup


def parse_args():
    parser = ArgumentParser(
        description='Parse a crossword puzzle from HTML to use in a prototype.',
        formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('file',
                        type=FileType(),
                        help='HTML file to load puzzle from.')
    return parser.parse_args()


def main():
    dump_path = Path('dump')
    for i, file in enumerate(dump_path.glob('*.html')):
        html = file.read_text()
        soup = BeautifulSoup(html, 'html.parser')
        cell_count = 0
        black_count = 0
        for cell in soup.find_all('td', class_='puzzle_cell'):
            cell_count += 1
            classes = cell.attrs['class']
            if 'black_square' in classes:
                black_count += 1
        letter_count = cell_count - black_count
        remainder4 = letter_count % 4
        remainder5 = letter_count % 5
        print(f'{i}, {file}: {letter_count} out of {cell_count} are letters, '
              f'leaving remainders {remainder4} and {remainder5}.')
        # for clue in soup.find_all('div', class_='clue_text'):
        #     is_across = 'across' in clue.attrs['id']
        #     print(is_across, clue.attrs['data-x'], clue.attrs['data-y'], clue.text)


main()
