import os
import sys
import traceback
import typing
from pathlib import Path

from PySide6.QtCore import QSettings
from PySide6.QtGui import QFont, QPdfWriter, QPageSize, QPainter, QKeyEvent, Qt, QCloseEvent
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
        self.old_clues = {}
        self.base_title = self.windowTitle()

        font = QFont('Monospace')
        font.setStyleHint(QFont.TypeWriter)
        font.setPointSize(self.ui.grid_text.font().pointSize())
        for field in (ui.grid_text, ui.clues_text, ui.blocks_text):
            field.setFont(font)

        ui.grid_text.textChanged.connect(self.grid_changed)
        ui.grid_text.focused.connect(self.grid_changed)
        ui.blocks_text.textChanged.connect(self.blocks_changed)
        ui.blocks_text.focused.connect(self.blocks_changed)
        ui.clues_text.textChanged.connect(self.clues_changed)

        self.state_fields = (self.ui.grid_text,
                             self.ui.clues_text,
                             self.ui.blocks_text)
        self.clean_state = self.current_state = self.build_current_state()

    def closeEvent(self, event: QCloseEvent):
        if not self.is_state_dirty():
            return  # Default behaviour: window will close.
        choice = QMessageBox.warning(self,
                                     'Unsaved Changes',
                                     'Changes have not been saved. Are you '
                                     'sure you want to quit?',
                                     QMessageBox.Ok | QMessageBox.Cancel)
        if choice == QMessageBox.Cancel:
            event.ignore()

    def build_current_state(self) -> typing.Dict[str, str]:
        state = {}
        for field in self.state_fields:
            state[field.objectName()] = field.toPlainText()
        return state

    def is_state_changed(self) -> bool:
        """ Has the state changed since the last time this was called?

        Also mark the window title with an asterisk if the state has changed
        since the file was saved.
        """
        new_state = self.build_current_state()
        suffix = '*' if new_state != self.clean_state else ''
        self.setWindowTitle(self.base_title + suffix)

        if new_state == self.current_state:
            return False

        self.current_state = new_state
        return True

    def is_state_dirty(self) -> bool:
        """ Has the state changed since it was saved? """
        self.is_state_changed()  # Update current state.

        return self.current_state != self.clean_state

    def on_error(self, ex_type, value, tb):
        traceback.print_exception(ex_type, value, tb)
        QMessageBox.warning(self,
                            str(ex_type.__name__),
                            str(value))

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() != Qt.Key_Insert:
            return
        overwrite_mode = not self.ui.grid_text.overwriteMode()
        for field in (self.ui.grid_text,
                      self.ui.clues_text,
                      self.ui.blocks_text):
            field.setOverwriteMode(overwrite_mode)

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
        self.ui.title_text.setText(puzzle.title)
        self.ui.grid_text.setPlainText(puzzle.format_grid())
        self.ui.clues_text.setPlainText(puzzle.format_clues())
        self.ui.blocks_text.setPlainText(puzzle.format_blocks())
        self.record_clean_state()

    def record_clean_state(self):
        self.clean_state = self.build_current_state()
        self.is_state_changed()  # Update dirty display.

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
        self.record_clean_state()

    def format_text(self) -> str:
        sections = [self.ui.title_text.text().strip() or 'Untitled']
        sections.extend(field.toPlainText().strip() or '-'
                        for field in (self.ui.grid_text,
                                      self.ui.clues_text,
                                      self.ui.blocks_text))
        return '\n\n'.join(sections)

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

        puzzle = self.parse_puzzle()
        puzzle.draw_blocks(painter)
        pdf.newPage()
        puzzle.draw_clues(painter)
        painter.end()

        self.statusBar().showMessage(f'Exported to {file_path.name}.')

    def parse_puzzle(self):
        puzzle = Puzzle.parse_sections(self.ui.title_text.text(),
                                       self.ui.grid_text.toPlainText(),
                                       self.ui.clues_text.toPlainText(),
                                       self.ui.blocks_text.toPlainText(),
                                       self.old_clues)
        return puzzle

    def grid_changed(self):
        if not self.is_state_changed():
            return
        puzzle = self.parse_puzzle()
        self.ui.clues_text.setPlainText(puzzle.format_clues())
        letter_count = puzzle.grid.letter_count
        remainder = letter_count % 4
        self.statusBar().showMessage(f'Grid has {letter_count} letters, '
                                     f'remainder {remainder}.')

    def blocks_changed(self):
        if not self.is_state_changed():
            return
        puzzle = self.parse_puzzle()
        block_summary = puzzle.display_block_sizes()
        if block_summary:
            self.statusBar().showMessage(f'Block sizes: {block_summary}.')

    def clues_changed(self):
        if not self.is_state_changed():
            return


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
