import os
import sys
import traceback
import typing
from pathlib import Path

from PySide6.QtCore import QSettings, QSize, QSizeF, QObject, QRectF
from PySide6.QtGui import QFont, QPdfWriter, QPageSize, QPainter, QKeyEvent, \
    Qt, QCloseEvent, QPixmap, QColor, QTextDocument, QTextFormat, QTextCursor, \
    QTextCharFormat, QPyTextObject
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QInputDialog

import four_letter_blocks
from four_letter_blocks.main_window import Ui_MainWindow
from four_letter_blocks.puzzle import Puzzle

DIAGRAM_TEXT_FORMAT = QTextFormat.UserObject + 1
DIAGRAM_DATA = 1
OBJECT_REPLACEMENT = chr(0xfffc)


class FourLetterBlocksWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ui = self.ui = Ui_MainWindow()
        ui.setupUi(self)

        ui.about_action.triggered.connect(self.about)
        ui.exit_action.triggered.connect(self.close)

        ui.new_action.triggered.connect(self.new_file)
        ui.open_action.triggered.connect(self.open)
        ui.save_action.triggered.connect(self.save)
        ui.save_as_action.triggered.connect(self.save_as)
        ui.export_action.triggered.connect(self.export)

        ui.shuffle_action.triggered.connect(self.shuffle)
        ui.options_action.triggered.connect(self.choose_font)

        sys.excepthook = self.on_error
        self.file_path: typing.Optional[Path] = None
        self.settings = get_settings()
        self.old_clues = {}
        self.base_title = self.windowTitle()

        ui.title_text.textChanged.connect(self.title_changed)
        ui.grid_text.textChanged.connect(self.grid_changed)
        ui.grid_text.focused.connect(self.grid_changed)
        ui.blocks_text.textChanged.connect(self.blocks_changed)
        ui.blocks_text.focused.connect(self.blocks_changed)
        ui.clues_text.textChanged.connect(self.clues_changed)

        self.state_fields = (self.ui.title_text,
                             self.ui.grid_text,
                             self.ui.clues_text,
                             self.ui.blocks_text)
        self.clean_state = self.current_state = self.build_current_state()
        self.update_font()

    def closeEvent(self, event: QCloseEvent):
        if self.can_abandon('quit'):
            return  # Default behaviour: window will close.
        event.ignore()

    def can_abandon(self, action: str):
        """ Confirm with the user that it's OK to lose current changes.

        :param action: describes the action the user asked for.
        :returns: True if the user confirmed or if there are no changes.
        """
        if not self.is_state_dirty():
            return True
        choice = QMessageBox.warning(self,
                                     'Unsaved Changes',
                                     f'Changes have not been saved. Are you '
                                     f'sure you want to {action}?',
                                     QMessageBox.Ok | QMessageBox.Cancel)
        return choice == QMessageBox.Ok

    def build_current_state(self) -> typing.Dict[str, str]:
        state = {}
        for field in self.state_fields:
            text_func = getattr(field, 'text', None)
            if text_func is None:
                text_func = field.toPlainText
            state[field.objectName()] = text_func()
        return state

    def is_state_changed(self) -> bool:
        """ Has the state changed since the last time this was called?

        Also mark the window title with an asterisk if the state has changed
        since the file was saved.
        """
        new_state = self.build_current_state()
        suffix = (' - ' + self.file_path.name) if self.file_path else ''
        suffix += '*' if new_state != self.clean_state else ''
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

    def new_file(self):
        if not self.can_abandon('start a new file'):
            return
        self.file_path = None
        self.ui.title_text.clear()
        self.ui.grid_text.clear()
        self.ui.clues_text.clear()
        self.ui.blocks_text.clear()
        self.record_clean_state()

    def open(self):
        if not self.can_abandon('open a file'):
            return
        save_dir = self.get_save_dir()
        kwargs = get_file_dialog_options()
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            'Open puzzle',
            dir=save_dir,
            filter='Text files (*.txt);;All files (*.*)',
            **kwargs)
        if not file_name:
            return

        self.settings.setValue('save_path', file_name)
        self.open_file(Path(file_name))

    def open_file(self, file_path: Path):
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
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            'Save puzzle',
            dir=save_dir,
            filter='Text files (*.txt);;All files (*.*)',
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
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            'Export puzzle',
            dir=save_dir,
            filter=';;'.join(('PDF blocks and clues (*.pdf)',
                              'PNG blocks (*.png)',
                              'Markdown text clues (*.md)',
                              'All files (*.*)')),
            **kwargs)
        if not file_name:
            return
        self.settings.setValue('save_path', file_name)
        file_path = Path(file_name)
        if file_path.suffix.lower() == '.pdf':
            self.export_pdf(file_path)
        elif file_path.suffix.lower() == '.png':
            self.export_png(file_path)
        else:
            self.export_md(file_path)

    def export_pdf(self, file_path: Path):
        file_name = str(file_path)
        pdf = QPdfWriter(file_name)
        pdf.setPageSize(QPageSize.Letter)

        puzzle = self.parse_puzzle()

        document = QTextDocument()
        document.setPageSize(QSize(pdf.width(), pdf.height()))
        font = document.defaultFont()
        font.setPixelSize(pdf.height()//60)
        document.setDefaultFont(font)
        puzzle.build_clues(document)

        diagram_handler = BlockDiagram(puzzle)
        doc_layout = document.documentLayout()
        doc_layout.registerHandler(DIAGRAM_TEXT_FORMAT, diagram_handler)

        cursor = QTextCursor(document)
        cursor.movePosition(cursor.End)
        cursor.insertText('\n')

        diagram_format = QTextCharFormat()
        diagram_format.setObjectType(DIAGRAM_TEXT_FORMAT)

        for i in range(len(puzzle.row_heights())):
            diagram_format.setProperty(DIAGRAM_DATA, i)
            cursor.insertText(OBJECT_REPLACEMENT, diagram_format)
            cursor.insertText('\n')

        document.print_(pdf)

        self.statusBar().showMessage(f'Exported to {file_path.name}.')

    def export_png(self, file_path: Path):
        puzzle = self.parse_puzzle()
        width, height = 640, 2000
        pixmap = QPixmap(width, height)
        transparent = QColor(255, 255, 255, 0)
        pixmap.fill(transparent)
        painter = QPainter(pixmap)
        height = puzzle.draw_blocks(painter)
        painter.end()
        cropped = pixmap.copy(0, 0, width, height)
        cropped.toImage().save(str(file_path), 'png')

    def export_md(self, file_path: Path):
        puzzle = self.parse_puzzle()
        with file_path.open('w') as file:
            print(f'## {puzzle.title}', file=file)
            print(puzzle.build_hints(), file=file)
            print(file=file)
            print('Across  ', file=file)
            for clue in puzzle.across_clues:
                formatted_clue = f'**{clue.format_number()}.** {clue.text}  '
                print(formatted_clue, file=file)
            print(file=file)
            print('Down  ', file=file)
            for clue in puzzle.down_clues:
                formatted_clue = f'**{clue.format_number()}.** {clue.text}  '
                print(formatted_clue, file=file)

    def parse_puzzle(self):
        puzzle = Puzzle.parse_sections(self.ui.title_text.text(),
                                       self.ui.grid_text.toPlainText(),
                                       self.ui.clues_text.toPlainText(),
                                       self.ui.blocks_text.toPlainText(),
                                       self.old_clues)
        return puzzle

    def shuffle(self):
        puzzle = self.parse_puzzle()
        puzzle.shuffle()
        self.ui.blocks_text.setPlainText(puzzle.format_blocks())

    def grid_changed(self):
        if not self.is_state_changed():
            return
        puzzle = self.parse_puzzle()
        self.ui.clues_text.setPlainText(puzzle.format_clues())
        self.ui.blocks_text.setPlainText(puzzle.format_blocks())
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

    def title_changed(self):
        if not self.is_state_changed():
            return

    def choose_font(self):
        font_size = self.settings.value('font_size', 11, int)
        font_size, is_ok = QInputDialog.getInt(self,
                                               'Set Font Size',
                                               'Font size:',
                                               font_size,
                                               minValue=1)
        if is_ok:
            self.settings.setValue('font_size', font_size)
            self.update_font()

    def update_font(self):
        font_size = self.settings.value('font_size', 11, int)
        font = self.font()
        font.setPointSize(font_size)
        # for child in self.ui.menubar.children():
        #     child.setFont(font)
        self.setFont(font)

        font = QFont('Monospace')
        font.setStyleHint(QFont.TypeWriter)
        font.setPointSize(font_size)
        for target in (self.ui.grid_text,
                       self.ui.clues_text,
                       self.ui.blocks_text):
            target.setFont(font)


class BlockDiagram(QPyTextObject):
    def __init__(self, puzzle: Puzzle, parent: QObject = None):
        super().__init__(parent)
        self.puzzle = puzzle

    # noinspection PyPep8Naming,PyShadowingBuiltins
    def intrinsicSize(self,
                      doc: QTextDocument,
                      posInDocument: int,
                      format: QTextFormat) -> QSizeF:
        row_index = format.property(DIAGRAM_DATA)
        row_heights = self.puzzle.row_heights(doc.textWidth())
        row_height = row_heights[row_index]
        return QSizeF(doc.textWidth(), row_height)

    # noinspection PyPep8Naming,PyShadowingBuiltins
    def drawObject(self,
                   painter: QPainter,
                   rect: QRectF,
                   doc: QTextDocument,
                   posInDocument: int,
                   format: QTextFormat):
        row_index = format.property(DIAGRAM_DATA)
        self.puzzle.draw_blocks(painter,
                                row_index=row_index,
                                x=rect.x(),
                                y=rect.y())


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
