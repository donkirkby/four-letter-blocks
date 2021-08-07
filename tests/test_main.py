from PySide6.QtWidgets import QApplication

from four_letter_blocks.__main__ import FourLetterBlocksWindow


# noinspection PyUnusedLocal
def test_window_creation(qt_application: QApplication):
    window = FourLetterBlocksWindow()

    assert window.windowTitle() == 'Four-Letter Blocks'
