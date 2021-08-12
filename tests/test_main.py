from pathlib import Path

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication

from four_letter_blocks.__main__ import FourLetterBlocksWindow


# noinspection PyUnusedLocal
def test_window_creation(qt_application: QApplication):
    window = FourLetterBlocksWindow()

    assert window.windowTitle() == 'Four-Letter Blocks'


# noinspection PyUnusedLocal
def test_grid_changed(qt_application: QApplication):
    new_grid_text = 'ABC'
    expected_clues_text = 'ABC - '

    window = FourLetterBlocksWindow()

    window.ui.grid_text.setPlainText(new_grid_text)

    clues_text = window.ui.clues_text.toPlainText()

    assert clues_text == expected_clues_text


# noinspection PyUnusedLocal
def test_format_text(qt_application: QApplication):
    new_grid_text = 'ABC'
    expected_formatted_text = '''\
Untitled

ABC

ABC -

-'''

    window = FourLetterBlocksWindow()

    window.ui.grid_text.setPlainText(new_grid_text)

    formatted_text = window.format_text()

    assert formatted_text == expected_formatted_text


# noinspection PyUnusedLocal
def test_save_pdf(qt_application: QApplication, tmp_path: Path):
    text_path = tmp_path / 'input.txt'
    text_path.write_text('''
Untitled

ABCD

ABCD - Clue

XXXX
''')
    pdf_path = tmp_path / 'output.pdf'

    window = FourLetterBlocksWindow()

    window.open_file(text_path)

    window.export_pdf(pdf_path)

    assert pdf_path.exists()


# noinspection PyUnusedLocal
def test_save_png(qt_application: QApplication, tmp_path: Path):
    text_path = tmp_path / 'input.txt'
    text_path.write_text('''
Untitled

ABCD

ABCD -

XXXX
''')
    png_path = tmp_path / 'output.png'

    window = FourLetterBlocksWindow()

    window.open_file(text_path)

    window.export_png(png_path)

    image = QImage(str(png_path))

    assert image.size().toTuple() == (640, 120)


# noinspection PyUnusedLocal
def test_save_md(qt_application: QApplication, tmp_path: Path):
    text_path = tmp_path / 'input.txt'
    text_path.write_text('''
Untitled

ABCD
E###
F###
G###
H###

ABCD - Clue for abcd
AEFGH - Clue for aefgh

XXXX
Y###
Y###
Y###
Y###
''')
    expected_markdown = '''\
## Untitled
Clue numbers are shuffled: 1 Across might not be in the top left.

Across@@
**1.** Clue for abcd@@

Down@@
**1.** Clue for aefgh@@
'''.replace('@', ' ')
    md_path = tmp_path / 'output.md'

    window = FourLetterBlocksWindow()

    window.open_file(text_path)

    window.export_md(md_path)

    markdown = md_path.read_text()

    assert markdown == expected_markdown
