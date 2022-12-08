import os
import re
import sys
import traceback
import typing
from argparse import ArgumentParser, ArgumentDefaultsHelpFormatter, ONE_OR_MORE
from functools import partial
from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED, Path as ZipPath

from PySide6.QtCore import QSettings, QSize, QSizeF, QObject, QRectF, QRect, QPoint, QBuffer
from PySide6.QtGui import QFont, QPdfWriter, QPageSize, QPainter, QKeyEvent, \
    Qt, QCloseEvent, QPixmap, QColor, QTextDocument, QTextFormat, QTextCursor, \
    QTextCharFormat, QPyTextObject, QImage
from PySide6.QtSvg import QSvgGenerator
from PySide6.QtWidgets import QApplication, QMainWindow, QMessageBox, QFileDialog, QInputDialog, QToolTip, \
    QListWidgetItem, QPlainTextEdit, QPushButton

import four_letter_blocks
from four_letter_blocks.big_puzzle_pair import BigPuzzlePair
from four_letter_blocks.block_packer import BlockPacker
from four_letter_blocks.clue_painter import CluePainter
from four_letter_blocks.evo_packer import PackingFitnessCalculator
from four_letter_blocks.fill_thread import FillThread
from four_letter_blocks.line_deduper import LineDeduper
from four_letter_blocks.main_window import Ui_MainWindow
from four_letter_blocks.puzzle import Puzzle
from four_letter_blocks.puzzle_pair import PuzzlePair
from four_letter_blocks.puzzle_set import PuzzleSet

from four_letter_blocks import four_letter_blocks_rc

assert four_letter_blocks_rc  # Need to import this module to load resources.

DIAGRAM_TEXT_FORMAT = QTextFormat.UserObject + 1
DIAGRAM_DATA = 1
OBJECT_REPLACEMENT = chr(0xfffc)


def create_svg_generator(svg_buffer):
    generator = QSvgGenerator()
    generator.setOutputDevice(svg_buffer)
    generator.setSize(QSize(8250, 10500))
    generator.setResolution(1000)  # dots per inch
    generator.setViewBox(QRect(0, 0, 8250, 10500))
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
        ui.export_set_action.triggered.connect(self.export_set)
        ui.export_pair_action.triggered.connect(self.export_pair)

        ui.shuffle_action.triggered.connect(self.shuffle)
        ui.options_action.triggered.connect(self.choose_font)

        ui.crossword_files.currentRowChanged.connect(
            self.select_crossword_file)
        self.selected_crossword_file = -1
        self.select_crossword_file(-1)
        self.crossword_set: typing.Dict[str, Puzzle] = {}

        ui.add_button.clicked.connect(self.add_crosswords)
        ui.remove_button.clicked.connect(self.remove_crossword)
        ui.puzzle_set_fill_button.clicked.connect(self.fill_puzzle_set_blocks)
        ui.puzzle_set_clear_button.clicked.connect(self.clear_puzzle_set_blocks)

        sys.excepthook = self.on_error
        self.file_path: typing.Optional[Path] = None
        self.settings = get_settings()
        self.old_clues = {}
        self.old_blocks: typing.List[typing.List[str]] = []
        self.base_title = self.windowTitle()

        ui.title_text.textChanged.connect(self.title_changed)
        ui.grid_text.textChanged.connect(self.grid_changed)
        ui.grid_text.focused.connect(self.grid_changed)
        ui.blocks_text.textChanged.connect(self.blocks_changed)
        ui.blocks_text.focused.connect(self.blocks_changed)
        ui.clues_text.textChanged.connect(self.clues_changed)

        self.old_puzzle_set_blocks = ''
        ui.puzzle_set_blocks.textChanged.connect(self.puzzle_set_blocks_changed)

        ui.warnings_label.setVisible(False)

        ui.front_open_button.clicked.connect(partial(self.open_pair, 0))
        ui.back_open_button.clicked.connect(partial(self.open_pair, 1))
        ui.front_clear_button.clicked.connect(self.clear_front)
        ui.back_clear_button.clicked.connect(self.clear_back)
        ui.front_fill_button.clicked.connect(self.fill_front)
        ui.back_fill_button.clicked.connect(self.fill_back)
        ui.front_refill_button.clicked.connect(self.refill_front)
        self.pair_puzzles: typing.List[None | Puzzle] = [None, None]
        ui.back_blocks_text.textChanged.connect(self.back_blocks_changed)
        ui.front_blocks_text.textChanged.connect(self.front_blocks_changed)
        self.fill_thread: FillThread | None = None

        self.state_fields = (ui.title_text,
                             ui.grid_text,
                             ui.clues_text,
                             ui.blocks_text)
        self.clean_state = self.current_state = self.build_current_state()
        self.update_font()
        ui.main_tabs.currentChanged.connect(self.select_tab)
        self.select_tab(ui.main_tabs.currentIndex())

    def closeEvent(self, event: QCloseEvent):
        if self.can_abandon('quit'):
            if self.fill_thread is not None:
                self.fill_thread.requestInterruption()
                self.fill_thread.wait()
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

    def new_file(self):
        if not self.can_abandon('start a new file'):
            return
        self.file_path = None
        self.ui.title_text.clear()
        self.ui.grid_text.clear()
        self.ui.clues_text.clear()
        self.ui.blocks_text.clear()
        self.record_clean_state()
        self.old_clues.clear()
        self.old_blocks.clear()

    def add_crosswords(self):
        save_dir = self.get_save_dir()
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

        self.add_crossword_files(file_names)

    def add_crossword_files(self, file_names: typing.Sequence[str]):
        crossword_files = self.ui.crossword_files
        old_names = [((item := crossword_files.item(i)).text(), item.toolTip())
                     for i in range(crossword_files.count())]
        old_files = {file_name for text, file_name in old_names}

        new_names = []
        for file_name in file_names:
            if file_name in old_files:
                continue
            with open(file_name) as puzzle_file:
                puzzle = Puzzle.parse(puzzle_file)
            self.crossword_set[file_name] = puzzle
            new_names.append((puzzle.title + ' ' + puzzle.extras, file_name))
        new_names.sort()

        i = 0
        while new_names:
            new_name = new_names.pop(0)
            while i < len(old_names):
                old_name = old_names[i]
                if new_name < old_name:
                    old_names.insert(i, new_name)
                    new_text, new_file = new_name
                    new_item = QListWidgetItem(new_text)
                    new_item.setToolTip(new_file)
                    crossword_files.insertItem(i, new_item)
                    i += 1
                    break
                i += 1
            else:
                old_names.append(new_name)
                new_text, new_file = new_name
                new_item = QListWidgetItem(new_text)
                new_item.setToolTip(new_file)
                crossword_files.addItem(new_item)
                i += 1

        self.summarize_crossword_set()

    def open_pair(self, puzzle_index: int):
        side = ('front', 'back')[puzzle_index]
        save_dir = self.get_save_dir()
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
        self.open_pair_file(file_name, puzzle_index)

    def open_pair_file(self, file_name, puzzle_index):
        with open(file_name) as source_file:
            puzzle = Puzzle.parse(source_file)
        edit_field = (self.ui.front_name, self.ui.back_name)[puzzle_index]
        edit_field.setText(puzzle.title)
        blocks_field = (self.ui.front_blocks_text,
                        self.ui.back_blocks_text)[puzzle_index]
        blocks_field.setPlainText(puzzle.format_blocks())
        self.pair_puzzles[puzzle_index] = puzzle
        self.summarize_crossword_pair()

    def summarize_crossword_pair(self):
        info = '...'
        front_puzzle: Puzzle
        back_puzzle: Puzzle
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

    def calculate_needed_counts(self):
        front_puzzle: Puzzle
        back_puzzle: Puzzle
        front_puzzle, back_puzzle = self.pair_puzzles
        needed_counts = back_puzzle.flipped_shape_counts
        needed_counts.subtract(front_puzzle.shape_counts)
        return needed_counts

    def back_blocks_changed(self):
        new_puzzle = self.update_pair_blocks(self.pair_puzzles[1],
                                             self.ui.back_blocks_text)
        if new_puzzle is not None:
            self.pair_puzzles[1] = new_puzzle
            self.summarize_crossword_pair()

    def front_blocks_changed(self):
        new_puzzle = self.update_pair_blocks(self.pair_puzzles[0],
                                             self.ui.front_blocks_text)
        if new_puzzle is not None:
            self.pair_puzzles[0] = new_puzzle
            self.summarize_crossword_pair()

    def update_pair_blocks(self,
                           puzzle: Puzzle | None,
                           blocks_text: QPlainTextEdit) -> Puzzle | None:
        if self.fill_thread is not None:
            return
        if puzzle is None:
            return
        new_blocks = blocks_text.toPlainText()
        if puzzle.format_blocks() == new_blocks:
            return
        return Puzzle.parse_sections(puzzle.title,
                                     puzzle.format_grid(),
                                     puzzle.format_clues(),
                                     new_blocks)

    def clear_back(self):
        old_blocks = self.ui.back_blocks_text.toPlainText()
        new_blocks = re.sub(r'[^#\s]', '?', old_blocks)
        self.ui.back_blocks_text.setPlainText(new_blocks)

    def clear_front(self):
        old_blocks = self.ui.front_blocks_text.toPlainText()
        new_blocks = re.sub(r'[^#\s]', '?', old_blocks)
        self.ui.front_blocks_text.setPlainText(new_blocks)

    def fill_back(self):
        self.statusBar().showMessage('Filling back...')
        self.launch_fill(self.ui.back_fill_button, is_packing_back=True)

    def fill_front(self):
        self.statusBar().showMessage('Filling front...')
        self.launch_fill(self.ui.front_fill_button)

    def refill_front(self):
        if self.fill_thread is not None:
            self.interrupt_fill()
            return

        file_name = self.get_save_file_name(
            'Save refilled solutions',
            'Text files (*.txt);;All files (*.*)')
        if not file_name:
            return
        self.statusBar().showMessage('Refilling blocks...')

        self.launch_fill(self.ui.front_refill_button,
                         report_path=Path(file_name))

    def interrupt_fill(self):
        self.fill_thread.requestInterruption()
        self.reset_fill_buttons()
        self.statusBar().showMessage('Stopped filling.')
        self.fill_thread.wait()
        self.fill_thread = None

    def reset_fill_buttons(self):
        ui = self.ui
        for button in (ui.back_fill_button,
                       ui.front_fill_button,
                       ui.front_refill_button,
                       ui.puzzle_set_fill_button):
            if button is ui.front_refill_button:
                button.setText('Refill...')
            else:
                button.setText('Fill')
            button.setEnabled(True)

    def launch_fill(self,
                    clicked_button: QPushButton,
                    is_packing_back: bool = False,
                    report_path: Path = None,
                    fitness_calculator: PackingFitnessCalculator = None):
        if self.fill_thread is not None:
            self.interrupt_fill()
            return
        if fitness_calculator is None:
            front_puzzle, back_puzzle = self.pair_puzzles
        else:
            front_puzzle = None
            item = self.ui.crossword_files.item(self.selected_crossword_file)
            back_puzzle = self.crossword_set[item.toolTip()]
            is_packing_back = True
        self.fill_thread = FillThread(self,
                                      back_puzzle,
                                      front_puzzle,
                                      is_packing_back,
                                      report_path,
                                      fitness_calculator)
        self.fill_thread.status_update.connect(self.on_fill_update_status)
        self.fill_thread.completed.connect(self.on_fill_completed)
        self.fill_thread.start()
        for fill_button in (self.ui.back_fill_button,
                            self.ui.front_fill_button,
                            self.ui.front_refill_button,
                            self.ui.puzzle_set_fill_button):
            if fill_button is clicked_button:
                continue
            fill_button.setEnabled(False)
        clicked_button.setText('Stop')

    def on_fill_update_status(self,
                              status: str,
                              back_blocks: str,
                              front_blocks: str):
        self.statusBar().showMessage(status)
        if self.ui.puzzle_set_fill_button.isEnabled():
            self.ui.puzzle_set_blocks.setPlainText(back_blocks)
        else:
            self.ui.back_blocks_text.setPlainText(back_blocks)
            self.ui.front_blocks_text.setPlainText(front_blocks)

    def on_fill_completed(self,
                          is_filled: bool,
                          summary: str,
                          back_puzzle: Puzzle,
                          front_puzzle: Puzzle):
        self.fill_thread = None
        if self.ui.puzzle_set_fill_button.isEnabled():
            self.ui.puzzle_set_blocks.setPlainText(back_puzzle.format_blocks())
        elif is_filled:
            self.pair_puzzles[0] = front_puzzle
            self.pair_puzzles[1] = back_puzzle
            self.ui.back_blocks_text.setPlainText(back_puzzle.format_blocks())
            self.ui.front_blocks_text.setPlainText(front_puzzle.format_blocks())
        else:
            front_puzzle: Puzzle
            back_puzzle: Puzzle
            front_puzzle, back_puzzle = self.pair_puzzles
            self.ui.back_blocks_text.setPlainText(back_puzzle.format_blocks())
            self.ui.front_blocks_text.setPlainText(front_puzzle.format_blocks())
        self.reset_fill_buttons()
        self.statusBar().showMessage(summary)

    def build_puzzle_set(self) -> PuzzleSet:
        puzzles = []
        crossword_files = self.ui.crossword_files
        for i in range(crossword_files.count()):
            file_name = crossword_files.item(i).toolTip()
            puzzles.append(self.crossword_set[file_name])

        puzzle_set = PuzzleSet(*puzzles)
        return puzzle_set

    def summarize_crossword_set(self):
        puzzle_set = self.build_puzzle_set()
        self.statusBar().showMessage(puzzle_set.block_summary)

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

        # Clear blocks first, to avoid extra warnings.
        self.ui.blocks_text.setPlainText('')

        self.ui.title_text.setText(puzzle.title)
        self.ui.grid_text.setPlainText(puzzle.format_grid())
        self.ui.clues_text.setPlainText(puzzle.format_clues())
        self.ui.blocks_text.setPlainText(puzzle.format_blocks())
        self.old_clues.clear()
        self.old_blocks.clear()
        self.record_clean_state()

    def remove_crossword(self):
        if self.selected_crossword_file >= 0:
            item = self.ui.crossword_files.takeItem(
                self.selected_crossword_file)
            file_name = item.toolTip()
            del self.crossword_set[file_name]
            self.selected_crossword_file = self.ui.crossword_files.currentRow()
            self.summarize_crossword_set()

    def fill_puzzle_set_blocks(self):
        self.statusBar().showMessage('Filling puzzle set...')
        puzzle_set = self.build_puzzle_set()
        fitness_calculator = PackingFitnessCalculator()
        fitness_calculator.count_parities.update(puzzle_set.count_parities)
        fitness_calculator.count_diffs.update(puzzle_set.count_diffs)
        fitness_calculator.count_min.update(puzzle_set.count_min)
        fitness_calculator.count_max.update(puzzle_set.count_max)
        self.launch_fill(self.ui.puzzle_set_fill_button,
                         is_packing_back=True,
                         fitness_calculator=fitness_calculator)

    def clear_puzzle_set_blocks(self):
        blocks_text = self.ui.puzzle_set_blocks.toPlainText()
        cleared_text = re.sub(r'[^#\s]', '?', blocks_text)
        self.ui.puzzle_set_blocks.setPlainText(cleared_text)

    def record_clean_state(self):
        self.clean_state = self.build_current_state()
        self.is_state_changed()  # Update dirty display.

    def save_as(self):
        file_name = self.get_save_file_name(
            'Save puzzle',
            'Text files (*.txt);;All files (*.*)')
        if not file_name:
            return

        self.file_path = Path(file_name)
        self.save()

    def get_save_file_name(self, caption, file_filter):
        save_dir = self.get_save_dir()
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
        packer = BlockPacker(15, 19, tries=10_000_000, min_tries=1_000)
        puzzles = list(self.crossword_set.values())
        puzzles.sort(key=lambda p: (p.grid.width, p.title))
        start_hue = self.ui.background_hue.value()
        puzzle_set = PuzzleSet(*puzzles,
                               block_packer=packer,
                               start_hue=start_hue)
        svg_buffer = QBuffer()
        generator = create_svg_generator(svg_buffer)

        painter = LineDeduper(QPainter(generator))
        puzzle_set.square_size = generator.width() / 16
        nick_radius = 5  # DPI is 1000
        puzzle_set.draw_cuts(painter, nick_radius)
        painter.end()

        front_buffer = QBuffer()
        front_image = QImage(2475, 3150, QImage.Format_RGB32)
        painter = QPainter(front_image)
        puzzle_set.square_size = front_image.width() / 16
        background_colour = puzzle_set.puzzles[0].face_colour
        painter.setBackground(background_colour)
        puzzle_set.draw_background_pattern(painter,
                                           puzzle_set.square_size / 6,
                                           x_offset=puzzle_set.square_size // 2,
                                           y_offset=puzzle_set.square_size // 2)
        puzzle_set.draw_front(painter)
        painter.end()
        success = front_image.save(front_buffer, 'PNG')
        assert success

        back_buffer = QBuffer()
        back_image = QImage(2475, 3150, QImage.Format_RGB32)
        painter = QPainter(back_image)
        painter.setBackground(background_colour)
        puzzle_set.draw_background_pattern(painter,
                                           puzzle_set.square_size / 6,
                                           x_offset=puzzle_set.square_size // 2,
                                           y_offset=puzzle_set.square_size // 2)
        puzzle_set.draw_back(painter)
        painter.end()
        success = back_image.save(back_buffer, 'PNG')
        assert success

        """ Booklet page images are 1575 x 2475. Safety margin is 75 pixels on
        every side. """
        page_buffers = []
        paper = QPixmap(':/paper.jpg')
        clue_painter = CluePainter(
            *puzzles,
            font_size=56,
            margin=75,
            intro_text='Solve each crossword puzzle with the pieces that match '
                       'the colour of the clue numbers. Good luck!\n',
            footer_text='https://donkirkby.github.io/four-letter-blocks',
            background=background_colour)
        page_image = QImage(1575, 2475, QImage.Format_RGB32)
        while not clue_painter.is_finished:
            painter = QPainter(page_image)
            painter.drawPixmap(0, 0, paper)
            clue_painter.draw_page(painter)
            painter.end()
            page_buffer = QBuffer()
            success = page_image.save(page_buffer, 'PNG')
            assert success
            page_buffers.append(page_buffer)

        with ZipFile(file_name, 'w', compression=ZIP_DEFLATED) as zip_file:
            zip_file.writestr('cuts.svg', svg_buffer.data())
            zip_file.writestr('front.png', front_buffer.data())
            zip_file.writestr('back.png', back_buffer.data())
            for page_number, page_buffer in enumerate(page_buffers, 1):
                zip_file.writestr(f'page{page_number}.png', page_buffer.data())

        self.statusBar().showMessage(f'Exported to {file_name}.')

    def export_pair(self):
        front_puzzle: Puzzle
        back_puzzle: Puzzle
        front_puzzle, back_puzzle = self.pair_puzzles
        assert front_puzzle is not None
        assert back_puzzle is not None

        save_dir = self.get_save_dir()
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

    def export_pair_file(self, file_name):
        front_puzzle: Puzzle
        back_puzzle: Puzzle
        front_puzzle, back_puzzle = self.pair_puzzles
        try:
            with ZipFile(file_name) as zip_file:
                packing = ZipPath(zip_file, 'packing.txt').read_text()
        except IOError:
            packing = None
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
                                     packer,
                                     start_hue=start_hue)
            square_coefficient = 1 / (grid_size + 3)
            font_coefficient = 1 / 39
        else:
            packer.split_row = grid_size // 2
            puzzle_pair = BigPuzzlePair(front_puzzle,
                                        back_puzzle,
                                        packer,
                                        start_hue=start_hue)
            square_coefficient = 1 / (grid_size - 1)
            font_coefficient = 1 / 30
        puzzle_pair.tab_count = 2
        front_bg = puzzle_pair.puzzles[0].face_colour
        puzzle_pair.puzzles[0].face_colour = QColor('transparent')
        back_bg = puzzle_pair.puzzles[1].face_colour
        puzzle_pair.puzzles[1].face_colour = QColor('transparent')

        zip_contents = {}  # {file_name: data}
        for puzzle_pair.slug_index in range(puzzle_pair.slug_count):
            front_buffer = QBuffer()
            front_image = QImage(2475, 3150, QImage.Format_RGB32)
            painter = QPainter(front_image)
            try:
                rotate_painter(painter)
                puzzle_pair.square_size = int(front_image.width() *
                                              square_coefficient)
                font_size = int(front_image.width() * font_coefficient)
                grid_rect = puzzle_pair.draw_front(painter, font_size)
                header_fraction = grid_rect.top() / front_image.width()
                painter.setBackground(front_bg)
                puzzle_pair.draw_background_pattern(painter,
                                                    puzzle_pair.square_size / 6,
                                                    x_offset=grid_rect.top(),
                                                    y_offset=grid_rect.left())
                # painter.eraseRect(painter.window())
                puzzle_pair.draw_front(painter, font_size)
                # puzzle_pair.draw_cuts(painter, header_fraction=header_fraction)
            finally:
                painter.end()
            success = front_image.save(front_buffer, 'PNG')
            assert success

            back_buffer = QBuffer()
            back_image = QImage(2475, 3150, QImage.Format_RGB32)
            painter = QPainter(back_image)
            try:
                painter.setBackground(back_bg)
                puzzle_pair.draw_background_pattern(painter,
                                                    puzzle_pair.square_size / 6,
                                                    x_offset=grid_rect.top(),
                                                    y_offset=grid_rect.left())
                # painter.eraseRect(painter.window())
                rotate_painter(painter, -90)
                puzzle_pair.draw_back(painter, font_size)
            finally:
                painter.end()
            success = back_image.save(back_buffer, 'PNG')
            assert success

            svg_buffer = QBuffer()
            generator = create_svg_generator(svg_buffer)
            painter = LineDeduper(QPainter(generator))
            try:
                rotate_painter(painter)
                puzzle_pair.square_size = int(generator.width() *
                                              square_coefficient)
                nick_radius = 5  # DPI is 1000
                puzzle_pair.draw_cuts(painter, nick_radius, header_fraction)
            finally:
                painter.end()
            slug_index = puzzle_pair.slug_index
            zip_contents[f'cuts{slug_index}.svg'] = svg_buffer.data()
            zip_contents[f'front{slug_index}.png'] = front_buffer.data()
            zip_contents[f'back{slug_index}.png'] = back_buffer.data()

        with ZipFile(file_name, 'w', compression=ZIP_DEFLATED) as zip_file:
            for name, data in zip_contents.items():
                zip_file.writestr(name, data)
            zip_file.writestr('packing.txt', puzzle_pair.block_packer.display())

        self.statusBar().showMessage(f'Exported to {file_name}.')

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
        cursor.movePosition(QTextCursor.End)
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
        cropped.toImage().save(str(file_path), 'png')

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
        file_name = self.ui.crossword_files.currentItem().toolTip()
        old_puzzle = self.crossword_set[file_name]
        new_puzzle = Puzzle.parse_sections(old_puzzle.title,
                                           old_puzzle.format_grid(),
                                           old_puzzle.format_clues(),
                                           blocks_text)
        self.crossword_set[file_name] = new_puzzle
        self.summarize_crossword_set()

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

    def select_tab(self, tab_index):
        is_single = tab_index == 0
        is_pair = tab_index == 1
        is_set = tab_index == 2
        self.ui.new_action.setEnabled(is_single)
        self.ui.open_action.setEnabled(is_single)
        self.ui.save_action.setEnabled(is_single)
        self.ui.save_as_action.setEnabled(is_single)
        self.ui.shuffle_action.setEnabled(is_single)
        self.ui.export_action.setEnabled(is_single)
        self.ui.export_pair_action.setEnabled(is_pair)
        self.ui.export_set_action.setEnabled(is_set)
        if is_single:
            puzzle = self.parse_puzzle()
            block_summary = puzzle.display_block_summary()
            self.statusBar().showMessage(block_summary)
        elif is_pair:
            self.summarize_crossword_pair()
        else:
            self.summarize_crossword_set()

    def select_crossword_file(self, file_index):
        self.selected_crossword_file = file_index
        is_enabled = file_index >= 0
        self.ui.remove_button.setEnabled(is_enabled)
        if not is_enabled:
            self.ui.puzzle_set_blocks.setPlainText('')
        else:
            file_name = self.ui.crossword_files.item(file_index).toolTip()
            puzzle = self.crossword_set[file_name]
            self.ui.puzzle_set_blocks.setPlainText(puzzle.format_blocks())

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
                       self.ui.blocks_text,
                       self.ui.back_blocks_text,
                       self.ui.front_blocks_text,
                       self.ui.puzzle_set_blocks):
            target.setFont(font)


class BlockDiagram(QPyTextObject):
    def __init__(self, puzzle: Puzzle,
                 position_map: typing.Dict = None,
                 parent: QObject = None):
        super().__init__(parent)
        self.puzzle = puzzle
        self.position_map = position_map

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


def parse_args():
    parser = ArgumentParser(description='Edit and export puzzles.',
                            formatter_class=ArgumentDefaultsHelpFormatter)
    parser.add_argument('--pair',
                        nargs=2,
                        help='Back and front puzzle files to export as a pair.')
    parser.add_argument('--set',
                        nargs=ONE_OR_MORE,
                        help='Set of puzzles to export together.')
    parser.add_argument('--hue',
                        type=int,
                        default=0,
                        help='Background hue.')
    parser.add_argument('-o', '--output',
                        help='Output file to export to.')
    args = parser.parse_args()
    if args.pair is not None and args.output is None:
        parser.error('Output is required when pair is given.')
    return args


def main():
    args = parse_args()
    app = QApplication()
    window = FourLetterBlocksWindow()
    done = False
    window.ui.background_hue.setValue(args.hue)
    window.ui.front_hue.setValue(args.hue)

    if args.pair is not None:
        back_file, front_file = args.pair
        window.open_pair_file(back_file, 1)
        window.open_pair_file(front_file, 0)
        window.export_pair_file(args.output)
        done = True

    if args.set is not None:
        window.add_crossword_files(args.set)
        window.export_set_file(args.output)
        done = True

    if not done:
        window.show()
        exit(app.exec())


if __name__ == '__main__':
    main()
