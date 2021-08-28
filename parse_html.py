from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter
from datetime import datetime
from pathlib import Path
from time import sleep
from urllib.parse import urlencode
from urllib.request import urlopen

# noinspection PyPackageRequirements
from bs4 import BeautifulSoup

from four_letter_blocks.puzzle import Puzzle


def parse_args():
    parser = ArgumentParser(
        description='Parse a crossword puzzle from HTML to use in a prototype.',
        formatter_class=ArgumentDefaultsHelpFormatter)
    this_month = datetime.now()
    last_month = this_month.replace(month=this_month.month - 1).strftime('%Y-%m')
    parser.add_argument('start',
                        nargs='?',
                        default=last_month,
                        type=month,
                        help='First month to include')
    parser.add_argument('end',
                        nargs='?',
                        default=last_month,
                        type=month,
                        help='Last month to include')
    return parser.parse_args()


def month(text: str) -> datetime:
    return datetime.strptime(text, '%Y-%m')


def main():
    args = parse_args()
    current_month: datetime = args.start
    dump_path = Path(__file__).parent / 'dump'
    while current_month <= args.end:
        file_formatted_month = current_month.strftime('%Y-%m')
        file_name = f'thumbs-{file_formatted_month}.html'
        file_path = dump_path / file_name
        web_formatted_month = current_month.strftime('%-m/%Y')
        params = urlencode(dict(month=web_formatted_month))
        url = 'https://www.xwordinfo.com/Thumbs?' + params
        html = read_or_fetch(url, file_path)
        soup = BeautifulSoup(html, 'html.parser')
        for table in soup.find_all('table', class_='thumb'):
            puzzle_date_text = table.attrs['data-tdate']
            constructor = table.attrs['data-ttcon']
            caption = table.find('caption')
            caption_text = caption.text.strip()
            grid = []
            letter_count = 0
            for y, row in enumerate(table.find_all('tr')):
                letters = []
                for x, cell in enumerate(row.find_all('td')):
                    letter = cell.text
                    if letter != '':
                        letter_count += 1
                    else:
                        letter = '#'
                    letters.append(letter)
                row_text = ''.join(letters)
                grid.append(row_text)
            if letter_count % 4 == 0:
                title = f'{caption_text} by {constructor}'
                grid_text = '\n'.join(grid)
                parse_puzzle(puzzle_date_text, title, grid_text, dump_path)
        current_month = current_month.replace(month=current_month.month+1)


def read_or_fetch(url: str, file_path: Path) -> str:
    if not file_path.exists():
        sleep(10)  # Throttle
        response = urlopen(url)
        html_bytes = response.read()
        with file_path.open('wb') as file:
            file.write(html_bytes)
    html = file_path.read_text()
    return html


def parse_puzzle(puzzle_date_text: str,
                 title: str,
                 grid_text: str,
                 dump_path: Path):
    puzzle_date = datetime.strptime(puzzle_date_text, '%m/%d/%Y')
    save_name = puzzle_date.strftime('puzzle-%Y-%m-%d')
    download_path: Path = dump_path / (save_name + '.html')
    params = urlencode(dict(date=puzzle_date_text))
    url = 'https://www.xwordinfo.com/Crossword?' + params
    html = read_or_fetch(url, download_path)
    soup = BeautifulSoup(html, 'html.parser')
    clues = []
    for group_div in soup.find_all('div', class_='numclue'):
        for child_div in group_div.find_all('div'):
            link = child_div.find('a')
            if not link:
                continue
            word = link.text
            clue = ' '.join(child_div.find_all(text=True, recursive=False))
            clue = clue.rstrip(' :')
            clues.append(f'{word} - {clue}')
    clues.sort()
    clues_text = '\n'.join(clues)
    puzzle = Puzzle.parse_sections(title, grid_text, clues_text, '')
    broken_clues = [word
                    for word, clue in puzzle.all_clues.items()
                    if clue.text == '']
    if broken_clues:
        print(f'Broken: {title}', *broken_clues)
        return

    puzzle_path = dump_path / (save_name + '.txt')
    with puzzle_path.open('w') as puzzle_file:
        puzzle_file.write(title)
        puzzle_file.write('\n\n')
        puzzle_file.write(grid_text)
        puzzle_file.write('\n\n')
        puzzle_file.write(clues_text)
    print('Saved:', title)


main()
