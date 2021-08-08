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
