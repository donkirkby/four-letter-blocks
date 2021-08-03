import os
import sys
import traceback
import typing
from io import StringIO
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtGui import QFont, QPdfWriter, QPageSize, QPainter
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog

import four_letter_blocks
from four_letter_blocks.main_window import Ui_MainWindow
from four_letter_blocks.puzzle import Puzzle


class FourLetterBlocksWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ui = self.ui = Ui_MainWindow()
        ui.setupUi(self)

        ui.about_action.triggered.connect(self.about)
        ui.exit_action.triggered.connect(self.close)

        ui.open_action.triggered.connect(self.open)
        ui.save_action.triggered.connect(self.save)
        ui.save_as_action.triggered.connect(self.save_as)
        ui.export_action.triggered.connect(self.export)

        sys.excepthook = self.on_error
        self.file_path: typing.Optional[Path] = None
        self.settings = get_settings()

        font = QFont('Monospace')
        font.setStyleHint(QFont.TypeWriter)
        font.setPointSize(self.ui.grid_text.font().pointSize())
        for field in (ui.grid_text, ui.clues_text, ui.blocks_text):
            field.setFont(font)

    def on_error(self, ex_type, value, tb):
        traceback.print_exception(ex_type, value, tb)
        QMessageBox.warning(self,
                            str(ex_type.__name__),
                            str(value))

    def about(self):
        QMessageBox.about(self,
                          'About Four-Letter Blocks',
                          f'Version {four_letter_blocks.__version__}')

    def open(self):
        save_dir = self.get_save_dir()
        kwargs = get_file_dialog_options()
        file_name, _ = QFileDialog.getOpenFileName(self,
                                                   'Open puzzle',
                                                   dir=save_dir,
                                                   filter='Text files (*.txt)',
                                                   **kwargs)
        if not file_name:
            return

        file_path = Path(file_name)
        self.settings.setValue('save_path', str(file_path))
        with file_path.open() as source_file:
            puzzle = Puzzle.parse(source_file)
        self.file_path = file_path
        self.ui.grid_text.setPlainText(puzzle.format_grid())
        self.ui.clues_text.setPlainText(puzzle.format_clues())
        self.ui.blocks_text.setPlainText(puzzle.format_blocks())

    def save_as(self):
        save_dir = self.get_save_dir()
        kwargs = get_file_dialog_options()
        file_name, _ = QFileDialog.getSaveFileName(self,
                                                   'Save puzzle',
                                                   dir=save_dir,
                                                   filter='Text files (*.txt)',
                                                   **kwargs)
        if not file_name:
            return
        self.file_path = Path(file_name)
        self.settings.setValue('save_path', str(self.file_path))

        self.save()

    def get_save_dir(self):
        save_path = self.settings.value('save_path')
        if save_path is None:
            return None
        save_path = Path(str(save_path))
        save_dir = str(save_path.parent)
        return save_dir

    def save(self):
        if self.file_path is None:
            self.save_as()
            return

        self.file_path.write_text(self.format_text())
        self.statusBar().showMessage(f'Saved to {self.file_path.name}.')

    def format_text(self) -> str:
        return '\n\n'.join(field.toPlainText().strip()
                           for field in (self.ui.grid_text,
                                         self.ui.clues_text,
                                         self.ui.blocks_text))

    def export(self):
        save_dir = self.get_save_dir()
        kwargs = get_file_dialog_options()
        file_name, _ = QFileDialog.getSaveFileName(self,
                                                   'Export puzzle',
                                                   dir=save_dir,
                                                   filter='PDF files (*.pdf)',
                                                   **kwargs)
        if not file_name:
            return
        file_path = Path(file_name)
        self.settings.setValue('save_path', file_name)
        pdf = QPdfWriter(file_name)
        pdf.setPageSize(QPageSize.Letter)
        painter = QPainter(pdf)

        puzzle = Puzzle.parse(StringIO(self.format_text()))
        puzzle.draw_blocks(painter)
        pdf.newPage()
        puzzle.draw_clues(painter)
        painter.end()

        self.statusBar().showMessage(f'Exported to {file_path.name}.')


def get_settings():
    settings = QSettings("Don Kirkby", "Four-Letter Blocks")
    return settings


def get_file_dialog_options():
    kwargs = {}
    if 'SNAP' in os.environ:
        # Native dialog restricts paths for snap processes to /run/user.
        kwargs['options'] = QFileDialog.DontUseNativeDialog
    return kwargs


def main():
    app = QApplication()
    window = FourLetterBlocksWindow()
    window.show()
    exit(app.exec())


if __name__ == '__main__':
    main()
