from enum import Enum, auto
import os
import re
import sys
import traceback
import typing
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, OPTIONAL
from functools import partial
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED

from PySide6.QtCore import QSettings, QSize, QSizeF, QObject, QRectF, QRect, \
    QPoint, QBuffer, QThread, QTimer
from PySide6.QtGui import QFont, QPdfWriter, QPageSize, QPainter, QKeyEvent, \
    Qt, QCloseEvent, QPixmap, QColor, QTextDocument, QTextFormat, QTextCursor, \
    QTextCharFormat, QPyTextObject, QImage
from PySide6.QtSvg import QSvgGenerator
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QInputDialog, QToolTip, \
    QListWidgetItem, QPlainTextEdit, QPushButton, QFontDialog

import four_letter_blocks
from four_letter_blocks.big_puzzle_pair import BigPuzzlePair
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.clue import Clue
from four_letter_blocks.clue_overflow import ClueOverflow
from four_letter_blocks.clue_painter import CluePainter
from four_letter_blocks.fill_thread import FillThread, PackingProgress
from four_letter_blocks.font_list_item import FontListItem
from four_letter_blocks.line_deduper import LineDeduper
from four_letter_blocks.main_window import Ui_MainWindow
from four_letter_blocks.one_sided_set import OneSidedSet
from four_letter_blocks.puzzle import Puzzle, RotationsDisplay
from four_letter_blocks.puzzle_pair import PuzzlePair
from four_letter_blocks.puzzle_set import PuzzleSet

from four_letter_blocks import four_letter_blocks_rc
from four_letter_blocks.set_loader import write_puzzle_set, read_puzzle_set

assert four_letter_blocks_rc  # Need to import this module to load resources.

DIAGRAM_TEXT_FORMAT = QTextFormat.UserObject + 1  # type:ignore[attr-defined]
DIAGRAM_DATA = 1
OBJECT_REPLACEMENT = chr(0xfffc)

class BlockType(Enum):
    PUZZLE = auto()
    TRAVEL = auto()


def create_svg_generator(svg_buffer):
    generator = QSvgGenerator()
    generator.setOutputDevice(svg_buffer)
    generator.setSize(QSize(594, 756))
    generator.setResolution(72)  # dots per inch
    generator.setViewBox(QRect(0, 0, 594, 756))
    return generator


def rotate_painter(painter: QPainter | LineDeduper, angle: int = 90):
    painter.rotate(angle)
    window = painter.window()
    if angle == 90:
        painter.translate(0, -window.width())
    else:
        assert angle == -90
        painter.translate(-window.height(), 0)
    painter.setWindow(0, 0, window.height(), window.width())
    painter.setViewport(painter.window())


class FourLetterBlocksWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        ui = self.ui = Ui_MainWindow()
        ui.setupUi(self)
        self.timer = QTimer()
        self.timer.setSingleShot(True)
        self.timer.setInterval(100)  # milliseconds
        self.timer.timeout.connect(self.blocks_timer_expired)
        self.is_front_modified = False
        self.is_back_modified = False

        self.pair_puzzles: typing.List[None | Puzzle] = [None, None]
        self.page_packers: list[BlockPacker] = []
        ui.main_tabs.setCurrentIndex(0)

        ui.about_action.triggered.connect(self.about)
        ui.exit_action.triggered.connect(self.close)

        ui.new_puzzle_action.triggered.connect(self.new_puzzle)
        ui.new_pair_action.triggered.connect(self.new_pair)
        ui.new_set_action.triggered.connect(self.new_set)
        ui.new_fonts_action.triggered.connect(self.new_fonts)
        ui.open_action.triggered.connect(self.open)
        ui.save_action.triggered.connect(self.save)
        ui.save_as_action.triggered.connect(self.save_as)
        ui.export_action.triggered.connect(self.export)
        ui.export_set_action.triggered.connect(self.export_set)
        ui.export_pair_action.triggered.connect(self.export_pair)
        ui.main_tabs.currentChanged.connect(self.select_tab)

        ui.shuffle_action.triggered.connect(self.shuffle)
        ui.options_action.triggered.connect(self.choose_font)

        ui.crossword_files.currentRowChanged.connect(
            self.select_crossword_file)
        self.selected_crossword_file = -1
        self.selected_puzzle: Puzzle | None = None
        self.select_crossword_file(-1)
        self.puzzle_set: PuzzleSet | None = None
        self.crossword_set: typing.Dict[str, Puzzle] = {}  # {file_name: puzzle}

        ui.add_button.clicked.connect(self.add_crosswords)
        ui.remove_button.clicked.connect(self.remove_crossword)
        ui.puzzle_set_fill_button.clicked.connect(self.fill_puzzle_set_blocks)
        ui.puzzle_set_clear_button.clicked.connect(self.clear_puzzle_set_blocks)

        ui.is_travel_blocks.clicked.connect(self.on_block_type_changed)
        ui.is_puzzle_blocks.clicked.connect(self.on_block_type_changed)
        ui.is_pair_travel_blocks.clicked.connect(self.on_block_type_changed)
        ui.is_pair_puzzle_blocks.clicked.connect(self.on_block_type_changed)

        ui.font_add_button.clicked.connect(self.add_font)
        ui.font_remove_button.clicked.connect(self.remove_font)
        ui.font_list.dropped.connect(self.font_list_changed)
        ui.one_sided_checkbox.setChecked(True)

        sys.excepthook = self.on_error
        self.file_path: typing.Optional[Path] = None
        self.settings = get_settings()
        self.old_clues: typing.Dict[str, Clue] = {}
        self.old_blocks: typing.List[typing.List[str]] = []
        self.base_title = self.windowTitle()

        font_list_text = self.settings.value('font_list', '')
        assert isinstance(font_list_text, str)
        for font_string in font_list_text.splitlines():
            font = QFont()
            font.fromString(font_string)
            item = FontListItem(font)
            ui.font_list.addItem(item)
        self.update_font_combo()

        ui.title_text.textChanged.connect(self.title_changed)
        ui.grid_text.textChanged.connect(self.grid_changed)
        ui.grid_text.focused.connect(self.grid_changed)
        ui.blocks_text.textChanged.connect(self.blocks_changed)
        ui.blocks_text.focused.connect(self.blocks_changed)
        ui.clues_text.textChanged.connect(self.clues_changed)

        self.old_puzzle_set_blocks = ''
        ui.puzzle_set_blocks.textChanged.connect(self.puzzle_set_blocks_changed)

        ui.warnings_label.setVisible(False)

        ui.front_open_button.clicked.connect(partial(self.open_pair_puzzle, 0))
        ui.back_open_button.clicked.connect(partial(self.open_pair_puzzle, 1))
        ui.front_clear_button.clicked.connect(self.clear_front)
        ui.back_clear_button.clicked.connect(self.clear_back)
        ui.front_fill_button.clicked.connect(self.fill_front)
        ui.front_refill_button.clicked.connect(self.refill_front)
        ui.back_blocks_text.textChanged.connect(self.back_blocks_changed)
        ui.front_blocks_text.textChanged.connect(self.front_blocks_changed)
        self.fill_thread: QThread | None = None

        self.state_fields = (ui.title_text,
                             ui.grid_text,
                             ui.clues_text,
                             ui.blocks_text)
        self.clean_state = self.current_state = self.build_current_state()
        self.update_font()
        self.on_block_type_changed()
        self.new_puzzle()
        self.select_tab()

    def closeEvent(self, event: QCloseEvent):
        if self.can_abandon('quit'):
            if self.fill_thread is not None:
                self.fill_thread.requestInterruption()
                self.fill_thread.wait()
            return  # Default behaviour: window will close.
        event.ignore()

    @property
    def block_type(self) -> BlockType:
        if self.ui.is_puzzle_blocks.isChecked():
            return BlockType.PUZZLE
        return BlockType.TRAVEL

    @property
    def pair_block_type(self) -> BlockType:
        if self.ui.is_pair_puzzle_blocks.isChecked():
            return BlockType.PUZZLE
        return BlockType.TRAVEL

    def can_abandon(self, action: str):
        """ Confirm with the user that it's OK to lose current changes.

        :param action: describes the action the user asked for.
        :returns: True if the user confirmed or if there are no changes.
        """
        if not self.is_state_dirty():
            return True
        buttons = QMessageBox.Ok | QMessageBox.Cancel  # type:ignore[attr-defined]
        ok_button = QMessageBox.Ok  # type:ignore[attr-defined]

        # noinspection PyTypeChecker
        choice = QMessageBox.warning(self,
                                     'Unsaved Changes',
                                     f'Changes have not been saved. Are you '
                                     f'sure you want to {action}?',
                                     buttons)  # type:ignore[call-arg]
        return choice == ok_button

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
                            str(value))  # type: ignore[warning]

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() != Qt.Key.Key_Insert:
            return
        overwrite_mode = not self.ui.grid_text.overwriteMode()
        for field in (self.ui.grid_text,
                      self.ui.clues_text,
                      self.ui.blocks_text,
                      self.ui.back_blocks_text,
                      self.ui.front_blocks_text,
                      self.ui.puzzle_set_blocks):
            field.setOverwriteMode(overwrite_mode)

    def on_rotations_display_changed(self):
        self.current_state = None
        self.blocks_changed()

    def about(self):
        QMessageBox.about(self,
                          'About Four-Letter Blocks',
                          f'Version {four_letter_blocks.__version__}')

    def new_puzzle(self):
        if not self.can_abandon('start a new puzzle'):
            return
        ui = self.ui
        ui.main_tabs.setCurrentWidget(ui.puzzle_tab)
        self.file_path = None
        ui.title_text.clear()
        ui.grid_text.clear()
        ui.clues_text.clear()
        ui.blocks_text.clear()
        self.record_clean_state()
        self.old_clues.clear()
        self.old_blocks.clear()


    def new_pair(self):
        if not self.can_abandon('start a new pair of puzzles'):
            return
        ui = self.ui
        ui.main_tabs.setCurrentWidget(ui.pair_tab)
        self.file_path = None
        self.record_clean_state()

    def new_set(self):
        if not self.can_abandon('start a new set of puzzles'):
            return
        ui = self.ui
        ui.main_tabs.setCurrentWidget(ui.set_tab)
        self.file_path = None
        self.record_clean_state()

    def new_fonts(self):
        if not self.can_abandon('edit font preferences'):
            return
        ui = self.ui
        ui.main_tabs.setCurrentWidget(ui.fonts_tab)
        self.file_path = None
        self.record_clean_state()

    def add_crosswords(self) -> None:
        save_dir = self.get_save_dir()
        assert save_dir is not None
        kwargs = get_file_dialog_options()
        file_names: typing.List[str]
        file_names, selected_filter = QFileDialog.getOpenFileNames(
            self,
            'Open Crossword Files',
            dir=save_dir,
            filter='Text files (*.txt);;All files (*.*)',
            **kwargs)
        if not file_names:
            return

        self.settings.setValue('save_path', file_names[0])
        self.add_crossword_files(file_names)

    def add_crossword_files(self, file_names: typing.Sequence[str]) -> None:
        puzzles = []
        for file_name in file_names:
            puzzle = Puzzle.parse_path(Path(file_name))
            puzzles.append(puzzle)
        self.add_crossword_objects(puzzles)

    def add_crossword_objects(self, puzzles: typing.Sequence[Puzzle]) -> None:
        crossword_files = self.ui.crossword_files
        old_names = [((item := crossword_files.item(i)).text(), item.toolTip())
                     for i in range(crossword_files.count())]
        old_files = {file_name for text, file_name in old_names}

        new_names = []
        for puzzle in puzzles:
            file_name = str(puzzle.source_path)
            if file_name in old_files:
                continue
            self.crossword_set[file_name] = puzzle
            new_names.append((puzzle.title + ' ' + puzzle.extras, file_name))

        while new_names:
            new_name = new_names.pop(0)
            old_names.append(new_name)
            new_text, new_file = new_name
            new_item = QListWidgetItem(new_text)
            new_item.setToolTip(new_file)
            crossword_files.addItem(new_item)

        self.summarize_crossword_set()

    def add_font(self) -> None:
        font: QFont
        is_ok, font = QFontDialog.getFont()
        if not is_ok:
            return

        font_size = self.settings.value('font_size', 11, int)
        assert isinstance(font_size, int)
        font.setPointSize(font_size)
        item = FontListItem(font)
        self.ui.font_list.addItem(item)
        self.update_font_combo()

    def remove_font(self):
        font_list = self.ui.font_list
        i = font_list.currentRow()
        if i < 0:
            return
        font_list.takeItem(i)
        self.update_font_combo()

    def font_list_changed(self):
        self.update_font_combo()

    def update_font_combo(self):
        font_strings = []
        for i in range(self.ui.font_list.count()):
            item = self.ui.font_list.item(i)
            font_strings.append(item.font().toString())

        font_text = '\n'.join(font_strings)
        self.settings.setValue('font_list', font_text)

        font_combo = self.ui.puzzle_set_font_list
        font_combo.clear()
        font_list = self.ui.font_list
        for i in range(font_list.count()):
            item = font_list.item(i)
            _, description = item.text().split(' - ', 1)
            font_combo.addItem(description, userData=item.font())

    def open_pair_puzzle(self, puzzle_index: int):
        side = ('front', 'back')[puzzle_index]
        save_dir = self.get_save_dir()
        assert save_dir is not None
        kwargs = get_file_dialog_options()
        file_name, _ = QFileDialog.getOpenFileName(
            self,
            f'Open {side} puzzle',
            dir=save_dir,
            filter='Text files (*.txt);;All files (*.*)',
            **kwargs)
        if not file_name:
            return

        self.settings.setValue('save_path', file_name)
        self.open_pair_puzzle_file(file_name, puzzle_index)

    def open_pair_puzzle_file(self, file_name, puzzle_index):
        puzzle = Puzzle.parse_path(Path(file_name))
        edit_field = (self.ui.front_name, self.ui.back_name)[puzzle_index]
        edit_field.setText(puzzle.title)
        blocks_field = (self.ui.front_blocks_text,
                        self.ui.back_blocks_text)[puzzle_index]
        blocks_field.setPlainText(puzzle.format_blocks())
        self.pair_puzzles[puzzle_index] = puzzle
        self.summarize_crossword_pair()

    def summarize_crossword_pair(self) -> None:
        info = '...'
        front_puzzle: Puzzle | None
        back_puzzle: Puzzle | None
        front_puzzle, back_puzzle = self.pair_puzzles
        is_export_enabled = False
        if not any(self.pair_puzzles):
            status = 'Open a pair of puzzles.'
        elif back_puzzle is None:
            status = 'Open a back puzzle.'
        elif front_puzzle is None:
            status = 'Open a front puzzle.'
        elif front_puzzle.grid.letter_count != back_puzzle.grid.letter_count:
            front_count = front_puzzle.grid.letter_count
            back_count = back_puzzle.grid.letter_count
            status = f'Front has {front_count} letters, back has {back_count}.'
        else:
            is_export_enabled = True
            needed_counts = self.calculate_needed_counts()
            needed_shapes = ', '.join(
                f'{shape}: {count}'
                for shape, count in sorted(needed_counts.items())
                if count != 0)
            messages = front_puzzle.check_style()
            messages.append('Needed shapes: ' + needed_shapes)
            info = '\n'.join(messages)
            status = front_puzzle.display_block_summary()

        self.ui.needed_shapes_label.setText(info)
        self.ui.export_pair_action.setEnabled(is_export_enabled)
        self.statusBar().showMessage(status)

    def calculate_needed_counts(self) -> typing.Counter[str]:
        front_puzzle: Puzzle | None
        back_puzzle: Puzzle | None
        front_puzzle, back_puzzle = self.pair_puzzles
        assert front_puzzle is not None
        assert back_puzzle is not None
        front_puzzle.rotations_display = RotationsDisplay.FRONT
        back_puzzle.rotations_display = RotationsDisplay.BACK
        needed_counts = back_puzzle.shape_counts
        needed_counts.subtract(front_puzzle.shape_counts)
        return needed_counts

    def back_blocks_changed(self):
        self.is_back_modified = True
        self.timer.start()



    def front_blocks_changed(self):
        self.is_front_modified = True
        self.timer.start()

    def update_pair_blocks(self,
                           puzzle_index: int,
                           blocks_text: QPlainTextEdit) -> Puzzle | None:
        if self.fill_thread is not None:
            return None
        if puzzle_index == 0 and self.pair_block_type == BlockType.TRAVEL:
            self.page_packers[0].load_start_text(blocks_text.toPlainText())
            return None
        puzzle = self.pair_puzzles[puzzle_index]
        if puzzle is None:
            return None
        new_blocks = blocks_text.toPlainText()
        if puzzle.format_blocks() == new_blocks:
            return None
        new_puzzle = Puzzle.parse_sections(puzzle.title,
                                           puzzle.format_grid(),
                                           puzzle.format_clues(),
                                           new_blocks)
        assert puzzle.source_path is not None
        new_puzzle.source_path = puzzle.source_path
        if new_puzzle is not None:
            self.pair_puzzles[puzzle_index] = new_puzzle
            self.summarize_crossword_pair()
            cursor = blocks_text.textCursor()
            old_position = cursor.position()
            blocks_text.setPlainText(new_puzzle.format_blocks())
            cursor.setPosition(old_position)
            blocks_text.setTextCursor(cursor)
        return new_puzzle

    def clear_back(self):
        old_blocks = self.ui.back_blocks_text.toPlainText()
        new_blocks = re.sub(r'[^#\s]', '?', old_blocks)
        self.ui.back_blocks_text.setPlainText(new_blocks)

    def clear_front(self):
        old_blocks = self.ui.front_blocks_text.toPlainText()
        new_blocks = re.sub(r'[^#\s]', '?', old_blocks)
        self.ui.front_blocks_text.setPlainText(new_blocks)

    def fill_front(self):
        ui = self.ui
        if ui.is_pair_puzzle_blocks.isChecked():
            target_texts = (ui.back_blocks_text.toPlainText().replace('.', '?'),
                            ui.front_blocks_text.toPlainText().replace('.', '?'))
            source_texts = ()
            message = 'Filling front and back...'
        else:
            target_texts = (ui.front_blocks_text.toPlainText()
                            .replace('.', '?').replace('#', '?'),)
            source_texts = (ui.back_blocks_text.toPlainText(),)
            message = 'Filling travel blocks...'
        self.statusBar().showMessage(message)
        new_thread = FillThread(target_texts, source_texts)
        self.launch_fill(self.ui.front_fill_button, new_thread)

    def refill_front(self):
        if self.fill_thread is not None:
            self.interrupt_fill()
            return

        file_name = self.get_save_file_name(
            'Save refilled solutions',
            'Log files (*.log);;All files (*.*)')
        if not file_name:
            return
        self.statusBar().showMessage('Refilling blocks...')

        # self.launch_fill(self.ui.front_refill_button,
        #                  report_path=Path(file_name))

    def interrupt_fill(self):
        if self.fill_thread is None:
            return

        self.fill_thread.requestInterruption()
        self.reset_fill_buttons()
        self.statusBar().showMessage('Stopped filling.')
        self.fill_thread.wait()
        self.fill_thread = None

    def reset_fill_buttons(self):
        ui = self.ui
        for button in (ui.front_fill_button,
                       ui.front_refill_button,
                       ui.puzzle_set_fill_button):
            if button is ui.front_refill_button:
                button.setText('Refill...')
            else:
                button.setText('Fill')
            button.setEnabled(True)

    def launch_fill(self,
                    clicked_button: QPushButton,
                    new_thread: FillThread):
        if self.fill_thread is not None:
            self.interrupt_fill()
            return
        self.fill_thread = new_thread
        if new_thread.parent() is None:
            new_thread.setParent(self)
        ui = self.ui
        new_thread.status_update.connect(self.on_fill_update_status)
        new_thread.completed.connect(self.on_fill_completed)
        for fill_button in (ui.front_fill_button,
                            ui.front_refill_button,
                            ui.puzzle_set_fill_button):
            if fill_button is clicked_button:
                continue
            fill_button.setEnabled(False)
        clicked_button.setText('Stop')
        new_thread.start()

    def on_fill_update_status(self,
                              status: PackingProgress):
        self.statusBar().showMessage(status.summary)
        ui = self.ui
        if ui.puzzle_set_fill_button.isEnabled():
            ui.puzzle_set_blocks.setPlainText(status.source_texts[0])
        else:
            assert ui.front_fill_button.isEnabled()
            if len(status.target_texts) == 1:
                ui.front_blocks_text.setPlainText(status.target_texts[0])
            else:
                ui.back_blocks_text.setPlainText(status.target_texts[0])
                ui.front_blocks_text.setPlainText(status.target_texts[1])

    def on_fill_completed(self,
                          progress: PackingProgress):
        self.on_fill_update_status(progress)
        self.fill_thread = None
        self.reset_fill_buttons()

    def build_puzzle_set(self) -> PuzzleSet:
        puzzles = []
        crossword_files = self.ui.crossword_files
        for i in range(crossword_files.count()):
            file_name = crossword_files.item(i).toolTip()
            puzzles.append(self.crossword_set[file_name])

        set_class: type[PuzzleSet]
        if self.ui.one_sided_checkbox.isChecked():
            page_count = (len(puzzles) + 1) // 2
            set_class = OneSidedSet
        else:
            page_count = (len(puzzles) + 3) // 4
            set_class = PuzzleSet
        while len(self.page_packers) > page_count:
            self.page_packers.pop()
        while len(self.page_packers) < page_count:
            if not self.page_packers:
                width = 14
                height = 18
            else:
                width = 15
                height = 19
            self.page_packers.append(BlockPacker(
                width,
                height,
                tries=10_000,
                min_tries=1))
        puzzle_set = set_class(*puzzles,
                               page_packers=self.page_packers,
                               start_hue=self.ui.background_hue.value(),
                               frame_lengths=[(9, 4), (9, 4, 2, 2)])
        return puzzle_set

    def summarize_crossword_set(self):
        if self.ui.crossword_files.count() == 0:
            self.statusBar().showMessage('Add some crossword files.')
            return
        puzzle_set = self.build_puzzle_set()
        self.statusBar().showMessage(puzzle_set.block_summary)
        self.puzzle_set = puzzle_set

    def open(self):
        if not self.can_abandon('open a file'):
            return
        save_dir = self.get_save_dir()
        assert save_dir is not None

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
        try:
            self.open_puzzle_set_file(file_path)
            self.file_path = file_path
            return
        except ValueError:
            pass  # Not a puzzle set, so try opening a single puzzle file.
        puzzle = Puzzle.parse_path(file_path)
        self.file_path = file_path

        # Clear blocks first, to avoid extra warnings.
        self.ui.blocks_text.setPlainText('')

        self.ui.title_text.setText(puzzle.title)
        self.ui.grid_text.setPlainText(puzzle.format_grid())
        self.ui.clues_text.setPlainText(puzzle.format_clues())
        self.ui.blocks_text.setPlainText(puzzle.format_blocks())
        self.old_clues.clear()
        self.old_blocks.clear()
        self.record_clean_state()

    def open_puzzle_set_file(self, file_path: Path):
        ui = self.ui
        puzzle_set = read_puzzle_set(file_path)
        if isinstance(puzzle_set, PuzzlePair):
            ui.main_tabs.setCurrentWidget(ui.pair_tab)
            ui.is_pair_puzzle_blocks.setChecked(True)
            front_path = puzzle_set.puzzles[0].source_path
            back_path = puzzle_set.puzzles[1].source_path
            self.open_pair_puzzle_file(front_path, 0)
            self.open_pair_puzzle_file(back_path, 1)
            self.page_packers = puzzle_set.page_packers
        else:
            ui.main_tabs.setCurrentWidget(ui.set_tab)
            ui.crossword_files.clear()
            self.page_packers = puzzle_set.page_packers
            self.add_crossword_objects(puzzle_set.puzzles)
        self.select_tab()

    def remove_crossword(self):
        if self.selected_crossword_file >= 0:
            item = self.ui.crossword_files.takeItem(
                self.selected_crossword_file)
            file_name = item.toolTip()
            del self.crossword_set[file_name]
            self.selected_crossword_file = self.ui.crossword_files.currentRow()
            self.summarize_crossword_set()

    def fill_puzzle_set_blocks(self):
        if self.fill_thread is not None:
            self.interrupt_fill()
            self.puzzle_set_blocks_changed()
            return

        file_name = self.get_save_file_name(
            'Record filled set solutions',
            'Log files (*.log);;All files (*.*)')
        if not file_name:
            return

        self.fill_puzzle_set_blocks_with_log(Path(file_name))

    def fill_puzzle_set_blocks_with_log(self, log_path: Path):
        raise NotImplementedError()
        # self.statusBar().showMessage('Filling puzzle set...')
        # puzzle_set = self.puzzle_set
        # assert puzzle_set is not None
        # page_packer = puzzle_set.page_packers[puzzle_set.page_index]
        # evo_packer = EvoPacker(start_text=page_packer.display(),
        #                        tries=page_packer.tries,
        #                        min_tries=page_packer.min_tries)
        # packed_shape_counts = evo_packer.packed_shape_counts
        # puzzle_shape_counts: Counter[str] = Counter()
        # page_puzzles = puzzle_set.page_puzzles[puzzle_set.page_index]
        # for puzzle in page_puzzles:
        #     puzzle.rotations_display = RotationsDisplay.FRONT
        #     puzzle_shape_counts += puzzle.shape_counts
        # puzzle_shape_counts -= packed_shape_counts
        # evo_packer.required_shape_counts = puzzle_shape_counts
        # self.fill_thread = PageFillThread(self, evo_packer, log_path)
        # self.fill_thread.status_update.connect(self.on_fill_update_status)
        # self.fill_thread.completed.connect(self.on_fill_completed)
        # self.fill_thread.start()
        # self.ui.puzzle_set_fill_button.setText('Stop')

    def clear_puzzle_set_blocks(self):
        blocks_text = self.ui.puzzle_set_blocks.toPlainText()
        cleared_text = re.sub(r'[^#\s]', '?', blocks_text)
        self.ui.puzzle_set_blocks.setPlainText(cleared_text)

    def on_block_type_changed(self):
        ui = self.ui
        if not ui.is_puzzle_blocks.isEnabled():
            ui.puzzle_set_blocks.setPlainText('')
        elif self.block_type == BlockType.PUZZLE:
            assert self.selected_puzzle is not None
            ui.puzzle_set_blocks.setPlainText(
                self.selected_puzzle.format_blocks())
        else:
            page_packer = self.selected_page_packer()
            ui.puzzle_set_blocks.setPlainText(page_packer.display())
        if not (ui.is_pair_puzzle_blocks.isEnabled() and self.page_packers):
            ui.front_blocks_text.setPlainText('')
        elif self.pair_block_type == BlockType.PUZZLE:
            front_puzzle = self.pair_puzzles[0]
            assert front_puzzle is not None
            ui.front_blocks_text.setPlainText(front_puzzle.format_blocks())
        else:
            page_packer = self.page_packers[0]
            ui.front_blocks_text.setPlainText(page_packer.display())

    def selected_page_packer(self) -> BlockPacker:
        if self.ui.one_sided_checkbox.isChecked():
            selected_page_index = self.selected_crossword_file // 2
        else:
            selected_page_index = self.selected_crossword_file // 4
        assert self.puzzle_set is not None
        self.puzzle_set.page_index = selected_page_index
        page_packer = self.puzzle_set.page_packers[selected_page_index]
        return page_packer

    def record_clean_state(self):
        self.clean_state = self.build_current_state()
        self.is_state_changed()  # Update dirty display.

    def save_as(self):
        ui = self.ui
        current_tab = ui.main_tabs.currentWidget()
        if current_tab == ui.puzzle_tab:
            caption = 'Save puzzle'
        elif current_tab == ui.set_tab:
            caption = 'Save puzzle set'
        else:
            assert current_tab == ui.pair_tab
            caption = 'Save puzzle pair'
        file_name = self.get_save_file_name(
            caption,
            'Text files (*.txt);;All files (*.*)')
        if not file_name:
            return

        self.file_path = Path(file_name)
        self.save()

    def get_save_file_name(self, caption, file_filter):
        save_dir = self.get_save_dir()
        assert save_dir is not None
        kwargs = get_file_dialog_options()
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            caption,
            dir=save_dir,
            filter=file_filter,
            **kwargs)
        self.settings.setValue('save_path', file_name)
        return file_name

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

        ui = self.ui
        current_tab = ui.main_tabs.currentWidget()
        if current_tab is ui.puzzle_tab:
            self.file_path.write_text(self.format_puzzle())
        elif current_tab is ui.pair_tab:
            pair = PuzzlePair(*self.pair_puzzles)
            pair.start_hue = ui.front_hue.value()
            pair.page_packers = self.page_packers
            write_puzzle_set(pair, self.file_path)
        elif current_tab is ui.set_tab:
            assert self.puzzle_set is not None
            write_puzzle_set(self.puzzle_set, self.file_path)
        else:
            raise RuntimeError("Current tab doesn't support saving yet.")
        self.statusBar().showMessage(f'Saved to {self.file_path.name}.')
        self.record_clean_state()

    def format_puzzle(self) -> str:
        sections = [self.ui.title_text.text().strip() or 'Untitled']
        sections.extend(field.toPlainText().strip() or '-'
                        for field in (self.ui.grid_text,
                                      self.ui.clues_text,
                                      self.ui.blocks_text))
        return '\n\n'.join(sections)

    def export(self):
        save_dir = self.get_save_dir()
        assert save_dir is not None

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
        file_suffix = file_path.suffix.lower()
        if file_suffix == '.pdf':
            self.export_pdf(file_path)
        elif file_suffix == '.png':
            self.export_png(file_path)
        else:
            self.export_md(file_path)
        self.statusBar().showMessage(f'Exported to {file_path.name}.')

    @staticmethod
    def is_field_filled(field, label, button):
        if field.text():
            return True
        message = f"Select a {label.text().lower()} before exporting."
        point = button.mapToGlobal(QPoint(0, 0))
        QToolTip.showText(point, message)
        return False

    def export_set(self):
        ui = self.ui
        if ui.crossword_files.count() < 2:
            point = ui.add_button.mapToGlobal(QPoint(0, 0))
            QToolTip.showText(point, "Add more crosswords before exporting.")
            return
        save_dir = self.get_save_dir()
        assert save_dir is not None

        kwargs = get_file_dialog_options()
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            'Export puzzle set',
            dir=save_dir,
            filter=';;'.join(('Zip files (*.zip)',
                              'All files (*.*)')),
            **kwargs)
        if not file_name:
            return
        self.settings.setValue('save_path', file_name)

        self.export_set_file(file_name)

    def export_set_file(self, file_name: str):
        puzzle_set = self.puzzle_set
        assert puzzle_set is not None
        puzzle_set.pack_puzzles()
        font_combo = self.ui.puzzle_set_font_list
        if font_combo.count() >= len(puzzle_set.puzzles):
            first_font = font_combo.currentIndex()
            for i, puzzle in enumerate(puzzle_set.puzzles):
                font = font_combo.itemData((i+first_font) % font_combo.count())
                puzzle.font = font
        background_colour = puzzle_set.puzzles[0].face_colour
        background_tile = None
        svg_buffers = []
        front_buffers = []
        back_buffers = []
        for page_index in range(puzzle_set.page_count):
            if page_index != 0:
                puzzle_set.page_index = page_index
                puzzle_set.pack_puzzles()
            svg_buffer = QBuffer()
            generator = create_svg_generator(svg_buffer)

            deduper = LineDeduper(QPainter(generator))
            puzzle_set.square_size = generator.width() / 16
            nick_radius = 5  # DPI is 1000
            puzzle_set.draw_cuts(deduper, nick_radius)
            deduper.end()
            svg_buffers.append(svg_buffer)

            front_buffer = QBuffer()
            front_image = QImage(2475, 3150, QImage.Format.Format_RGB32)
            painter = QPainter(front_image)
            puzzle_set.square_size = round(front_image.width() / 16)
            tile_size = puzzle_set.square_size / 6
            background_tile = puzzle_set.create_background_tile(round(tile_size),
                                                                background_colour)
            painter.setBackground(background_colour)
            puzzle_set.draw_background_pattern(painter,
                                               tile_size,
                                               x_offset=puzzle_set.square_size // 2,
                                               y_offset=puzzle_set.square_size // 2)
            puzzle_set.draw_front(painter)
            painter.end()
            success = front_image.save(front_buffer, 'PNG')  # type:ignore[call-overload]
            assert success
            front_buffers.append(front_buffer)

            back_buffer = QBuffer()
            back_image = QImage(2475, 3150, QImage.Format.Format_RGB32)
            painter = QPainter(back_image)
            painter.setBackground(background_colour)
            puzzle_set.draw_background_pattern(painter,
                                               tile_size,
                                               x_offset=puzzle_set.square_size // 2,
                                               y_offset=puzzle_set.square_size // 2)
            puzzle_set.draw_back(painter)
            painter.end()
            success = back_image.save(back_buffer, 'PNG')  # type:ignore[call-overload]
            assert success
            back_buffers.append(back_buffer)

        """ Booklet page images are 1575 x 2475. Safety margin is 75 pixels on
        every side. """
        page_buffers = []
        paper = QPixmap(':/paper.jpg')
        clue_painter = CluePainter(
            *puzzle_set.puzzles,
            font_size=56,
            margin=75,
            intro_text='Solve each set of crossword clues with the pieces that '
                       'match the colour of its title. Good luck!\n',
            footer_text=puzzle_set.LINK_TEXT,
            background=background_colour,
            background_tile=background_tile)
        page_image = QImage(1575, 2475, QImage.Format.Format_RGB32)
        while not clue_painter.is_finished:
            painter = QPainter(page_image)
            painter.drawPixmap(0, 0, paper)
            puzzle = puzzle_set.puzzles[clue_painter.puzzle_index]
            clue_painter.background = puzzle.face_colour
            clue_painter.draw_page(painter)
            painter.end()
            page_buffer = QBuffer()
            success = page_image.save(page_buffer, 'PNG')  # type:ignore[call-overload]
            assert success
            page_buffers.append(page_buffer)

        with ZipFile(file_name, 'w', compression=ZIP_DEFLATED) as zip_file:
            for page_number, (svg_buffer,
                              front_buffer,
                              back_buffer) in enumerate(zip(svg_buffers,
                                                            front_buffers,
                                                            back_buffers),
                                                        start=1):
                zip_file.writestr(f'cuts{page_number}.svg',
                                  svg_buffer.data().data())
                zip_file.writestr(f'front{page_number}.png',
                                  front_buffer.data().data())
                zip_file.writestr(f'back{page_number}.png',
                                  back_buffer.data().data())
            for page_number, page_buffer in enumerate(page_buffers, 1):
                zip_file.writestr(f'page{page_number}.png',
                                  page_buffer.data().data())

        self.statusBar().showMessage(f'Exported to {file_name}.')

    def export_pair(self) -> None:
        front_puzzle: Puzzle | None
        back_puzzle: Puzzle | None
        front_puzzle, back_puzzle = self.pair_puzzles
        assert front_puzzle is not None
        assert back_puzzle is not None

        save_dir = self.get_save_dir()
        assert save_dir is not None

        kwargs = get_file_dialog_options()
        file_name, _ = QFileDialog.getSaveFileName(
            self,
            'Export puzzle pair',
            dir=save_dir,
            filter=';;'.join(('Zip files (*.zip)',
                              'All files (*.*)')),
            **kwargs)
        if not file_name:
            return
        self.settings.setValue('save_path', file_name)
        self.export_pair_file(file_name)

    def export_pair_file(self, file_name: str) -> None:
        assert self.pair_puzzles is not None
        max_font = 2000
        min_font = 2
        self.export_sized_pair_file(file_name, min_font)  # Save packing.

        while min_font < max_font:
            font_size = (min_font + max_font + 1) // 2
            try:
                self.export_sized_pair_file(file_name, font_size)
                min_font = font_size
            except ClueOverflow:
                max_font = font_size - 1

    def export_sized_pair_file(self, file_name: str, font_size: int) -> None:
        front_puzzle: Puzzle | None
        back_puzzle: Puzzle | None
        front_puzzle, back_puzzle = self.pair_puzzles
        assert front_puzzle is not None
        assert back_puzzle is not None
        packing = self.page_packers[0].display()
        grid_size = front_puzzle.grid.width
        packer = BlockPacker(grid_size,
                             grid_size,
                             start_text=packing,
                             tries=10_000_000,
                             min_tries=1_000)
        start_hue = self.ui.front_hue.value()
        if grid_size <= 9:
            puzzle_pair = PuzzlePair(front_puzzle,
                                     back_puzzle,
                                     block_packer=packer,
                                     start_hue=start_hue)
            square_coefficient = 1 / (grid_size + 3)
        else:
            packer.split_row = grid_size // 2
            puzzle_pair = BigPuzzlePair(front_puzzle,
                                        back_puzzle,
                                        block_packer=packer,
                                        start_hue=start_hue)
            square_coefficient = 1 / (grid_size - 1)
        puzzle_pair.pack_puzzles()
        puzzle_pair.tab_count = 1
        front_bg = puzzle_pair.puzzles[0].face_colour
        puzzle_pair.puzzles[0].face_colour = QColor('transparent')
        back_bg = puzzle_pair.puzzles[1].face_colour
        puzzle_pair.puzzles[1].face_colour = QColor('transparent')

        zip_contents = {}  # {file_name: data}
        for puzzle_pair.slug_index in range(puzzle_pair.slug_count):
            front_buffer = QBuffer()
            front_image = QImage(2475, 3150, QImage.Format.Format_RGB32)
            painter = QPainter(front_image)
            try:
                rotate_painter(painter)
                puzzle_pair.square_size = int(front_image.width() *
                                              square_coefficient)
                grid_rect = puzzle_pair.draw_front(painter, font_size)
                header_fraction = grid_rect.top() / front_image.width()
                painter.setBackground(front_bg)
                puzzle_pair.draw_background_pattern(
                    painter,
                    puzzle_pair.square_size / 6,
                    x_offset=round(grid_rect.top()),
                    y_offset=round(grid_rect.left()))
                # painter.eraseRect(painter.window())
                puzzle_pair.draw_front(painter, font_size)
                # puzzle_pair.draw_cuts(painter, header_fraction=header_fraction)
            finally:
                painter.end()
            success = front_image.save(front_buffer, 'PNG')  # type:ignore[call-overload]
            assert success

            back_buffer = QBuffer()
            back_image = QImage(2475, 3150, QImage.Format.Format_RGB32)
            painter = QPainter(back_image)
            try:
                painter.setBackground(back_bg)
                puzzle_pair.draw_background_pattern(
                    painter,
                    puzzle_pair.square_size / 6,
                    x_offset=round(grid_rect.top()),
                    y_offset=round(grid_rect.left()))
                # painter.eraseRect(painter.window())
                rotate_painter(painter, -90)
                puzzle_pair.draw_back(painter, font_size)
            finally:
                painter.end()
            success = back_image.save(back_buffer, 'PNG')  # type:ignore[call-overload]
            assert success

            svg_buffer = QBuffer()
            generator = create_svg_generator(svg_buffer)
            deduper: QPainter = LineDeduper(QPainter(generator))  # type:ignore[assignment]
            try:
                rotate_painter(deduper)
                puzzle_pair.square_size = int(generator.width() *
                                              square_coefficient)
                nick_radius = 0.36  # DPI is 72
                puzzle_pair.draw_cuts(deduper, nick_radius, header_fraction)
            finally:
                deduper.end()
            slug_index = puzzle_pair.slug_index
            zip_contents[f'cuts{slug_index}.svg'] = svg_buffer.data().data()
            zip_contents[f'front{slug_index}.png'] = front_buffer.data().data()
            zip_contents[f'back{slug_index}.png'] = back_buffer.data().data()

        with ZipFile(file_name, 'w', compression=ZIP_DEFLATED) as zip_file:
            for name, data in zip_contents.items():
                zip_file.writestr(name, data)
            zip_file.writestr('packing.txt', puzzle_pair.block_packer.display())

        self.statusBar().showMessage(f'Exported to {file_name}.')

    def export_pdf(self, file_path: Path):
        file_name = str(file_path)
        pdf = QPdfWriter(file_name)
        pdf.setPageSize(QPageSize.PageSizeId.Letter)

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
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText('\n')

        diagram_format = QTextCharFormat()
        diagram_format.setObjectType(DIAGRAM_TEXT_FORMAT)

        for i in range(len(puzzle.row_heights())):
            diagram_format.setProperty(DIAGRAM_DATA, i)
            cursor.insertText(OBJECT_REPLACEMENT, diagram_format)
            cursor.insertText('\n')

        document.print_(pdf)

    def export_png(self, file_path: Path):
        puzzle = self.parse_puzzle()
        puzzle.face_colour = QColor('white')
        width, height = 640, 2000
        pixmap = QPixmap(width, height)
        transparent = QColor(255, 255, 255, 0)
        pixmap.fill(transparent)
        painter = QPainter(pixmap)
        height = puzzle.draw_blocks(painter)
        painter.end()
        cropped = pixmap.copy(0, 0, width, height)
        cropped.toImage().save(str(file_path), 'png')  # type: ignore

    def export_md(self, file_path: Path):
        puzzle = self.parse_puzzle()
        with file_path.open('w') as file:
            print(f'## {puzzle.title}', file=file)
            print(puzzle.build_hints(), file=file)
            print(file=file)
            print('Across  ', file=file)
            for clue in puzzle.across_clues:
                print(f'**{clue.format_number()}.** {clue.format_text()}  ',
                      file=file)
            print(file=file)
            print('Down  ', file=file)
            for clue in puzzle.down_clues:
                print(f'**{clue.format_number()}.** {clue.format_text()}  ',
                      file=file)

    def parse_puzzle(self):
        puzzle = Puzzle.parse_sections(self.ui.title_text.text(),
                                       self.ui.grid_text.toPlainText(),
                                       self.ui.clues_text.toPlainText(),
                                       self.ui.blocks_text.toPlainText(),
                                       self.old_clues,
                                       self.old_blocks)
        puzzle.source_path = self.file_path
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
        warnings = puzzle.check_style()
        self.ui.warnings_label.setVisible(bool(warnings))
        if warnings:
            warnings.insert(0, 'Warnings')
            self.ui.warnings_label.setText('\n  '.join(warnings))
        block_summary = puzzle.display_block_summary()
        if block_summary:
            self.statusBar().showMessage(block_summary)

    def puzzle_set_blocks_changed(self):
        blocks_text = self.ui.puzzle_set_blocks.toPlainText()
        if blocks_text == self.old_puzzle_set_blocks:
            return
        if self.fill_thread is not None:
            return
        self.old_puzzle_set_blocks = blocks_text
        if self.ui.is_travel_blocks.isChecked():
            page_packer = self.selected_page_packer()
            page_packer.load_start_text(blocks_text)
            return
        current_item = self.ui.crossword_files.currentItem()
        if current_item is None:
            return
        file_name = current_item.toolTip()
        old_puzzle = self.crossword_set[file_name]
        new_puzzle = Puzzle.parse_sections(old_puzzle.title,
                                           old_puzzle.format_grid(),
                                           old_puzzle.format_clues(),
                                           blocks_text)
        new_puzzle.source_path = old_puzzle.source_path
        self.crossword_set[file_name] = new_puzzle
        self.summarize_crossword_set()

    def blocks_timer_expired(self):
        ui = self.ui
        if self.is_front_modified:
            self.is_front_modified = False
            self.update_pair_blocks(0, ui.front_blocks_text)
        if self.is_back_modified:
            self.is_back_modified = False
            self.update_pair_blocks(1, ui.back_blocks_text)

    def clues_changed(self):
        if not self.is_state_changed():
            return

    def title_changed(self):
        if not self.is_state_changed():
            return

    def choose_font(self):
        font_size = self.settings.value('font_size', 11, int)
        assert isinstance(font_size, int)
        font_size, is_ok = QInputDialog.getInt(self,
                                               'Set Font Size',
                                               'Font size:',
                                               font_size,
                                               minValue=1)
        if is_ok:
            self.settings.setValue('font_size', font_size)
            self.update_font()

    def select_tab(self, _tab_index: int = 0) -> None:
        ui = self.ui
        current_tab = ui.main_tabs.currentWidget()
        is_single = current_tab == ui.puzzle_tab
        is_pair = current_tab == ui.pair_tab
        is_set = current_tab == ui.set_tab
        is_fonts = current_tab == ui.fonts_tab
        self.ui.shuffle_action.setEnabled(is_single)
        self.ui.export_action.setEnabled(is_single)
        self.ui.export_pair_action.setEnabled(is_pair)
        self.ui.export_set_action.setEnabled(is_set)
        if is_single:
            ui.main_title.setText('Puzzle')
            puzzle = self.parse_puzzle()
            block_summary = puzzle.display_block_summary()
            self.statusBar().showMessage(block_summary)
        elif is_pair:
            ui.main_title.setText('Puzzle Pair')
            self.summarize_crossword_pair()
        elif is_set:
            ui.main_title.setText('Puzzle Set')
            self.summarize_crossword_set()
        else:
            assert is_fonts
            ui.main_title.setText('Font Preferences')
        for widget in (ui.is_pair_puzzle_blocks, ui.is_pair_travel_blocks):
            widget.setEnabled(is_pair)

    def select_crossword_file(self, file_index):
        self.selected_crossword_file = file_index
        is_enabled = file_index >= 0
        ui = self.ui
        for widget in (ui.remove_button,
                       ui.puzzle_set_clear_button,
                       ui.puzzle_set_fill_button,
                       ui.is_travel_blocks,
                       ui.is_puzzle_blocks,
                       ui.puzzle_set_blocks):
            widget.setEnabled(is_enabled)
        if not is_enabled:
            self.selected_puzzle = None
        else:
            file_name = ui.crossword_files.item(file_index).toolTip()
            self.selected_puzzle = self.crossword_set[file_name]
        self.on_block_type_changed()

    def update_font(self):
        font_size = self.settings.value('font_size', 11, int)
        assert isinstance(font_size, int)
        font = self.font()
        font.setPointSize(font_size)
        # for child in self.ui.menubar.children():
        #     child.setFont(font)
        self.setFont(font)

        font = QFont('Monospace')
        font.setStyleHint(QFont.StyleHint.TypeWriter)
        font.setPointSize(font_size)
        ui = self.ui
        for target in (ui.grid_text,
                       ui.clues_text,
                       ui.blocks_text,
                       ui.back_blocks_text,
                       ui.front_blocks_text,
                       ui.puzzle_set_blocks):
            target.setFont(font)

        font_size = round(font_size * 1.5)
        font.setPointSize(font_size)
        ui.main_title.setFont(font)


class BlockDiagram(QPyTextObject):
    def __init__(self, puzzle: Puzzle,
                 position_map: typing.Dict | None = None,
                 parent: QObject | None = None):
        super().__init__(parent)
        self.puzzle = puzzle
        self.position_map = position_map

    # noinspection PyPep8Naming,PyShadowingBuiltins
    def intrinsicSize(self,
                      doc: QTextDocument,
                      posInDocument: int,
                      format: QTextFormat) -> QSizeF:
        row_index: int = format.property(DIAGRAM_DATA)
        row_heights = self.puzzle.row_heights(round(doc.textWidth()))
        row_height = row_heights[row_index]
        return QSizeF(doc.textWidth(), row_height)

    # noinspection PyPep8Naming,PyShadowingBuiltins,PyTypeHints
    def drawObject(self,
                   painter: QPainter,
                   rect: QRectF | QRect,
                   doc: QTextDocument,
                   posInDocument: int,
                   format: QTextFormat):
        row_index = format.property(DIAGRAM_DATA)
        self.puzzle.draw_blocks(painter,
                                row_index=row_index,
                                x=round(rect.x()),
                                y=round(rect.y()))


def get_settings():
    settings = QSettings("Don Kirkby", "Four-Letter Blocks")
    return settings


def get_file_dialog_options():
    kwargs = {}
    if 'SNAP' in os.environ:
        # Native dialog restricts paths for snap processes to /run/user.
        kwargs['options'] = QFileDialog.Option.DontUseNativeDialog
    return kwargs


def parse_args():
    parser = ArgumentParser(description='Edit and export puzzles.',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('file',
                        nargs=OPTIONAL,
                        type=Path,
                        help='File to open: puzzle or set')
    parser.add_argument('command',
                        choices=('open', 'fill', 'export'),
                        nargs=OPTIONAL,
                        default='open',
                        help='What to do with the file')
    parser.add_argument('output',
                        nargs=OPTIONAL,
                        type=Path,
                        help='Output file to export to.')
    args = parser.parse_args()
    if args.command != 'open' and args.output is None:
        parser.error(f'Output is required for {args.command} command.')
    return args


def main():
    args = parse_args()
    app = QApplication()
    window = FourLetterBlocksWindow()
    done = False
    if args.file is not None:
        window.open_file(args.file)
        if args.command == 'fill':
            window.fill_puzzle_set_blocks_with_log(args.output)
        elif args.command == 'export':
            if window.puzzle_set is not None:
                window.export_set_file(args.output)
            elif window.pair_puzzles is not None:
                window.export_pair_file(args.output)
            else:
                window.export_pdf(args.output)
            done = True

    if not done:
        window.show()
        exit(app.exec())


if __name__ == '__main__':
    main()
