import math
import typing

from PySide6.QtCore import QRectF
from PySide6.QtGui import QPainter, QFont, Qt, QFontMetricsF, QColor, QPen

from four_letter_blocks.clue import Clue
from four_letter_blocks.puzzle import Puzzle
from four_letter_blocks.square import Square, draw_gradient_rect


class CluePainter:
    def __init__(self,
                 *puzzles: Puzzle,
                 font_size: float = None,
                 margin: int = 0,
                 intro_text: str = '',
                 footer_text: str = '',
                 background: QColor = QColor.fromHsv(0, 0, 0, 0)):
        self.puzzles = puzzles
        self.font_size = font_size
        self.margin = margin
        self.puzzle_index = self.across_index = self.down_index = 0
        self.intro_text = intro_text
        self.footer_text = footer_text
        self.background = background

    @property
    def is_finished(self):
        return self.puzzle_index >= len(self.puzzles)

    def draw_page(self, painter: QPainter):
        """ Paint clues for a single page.

        Draw starting with whatever didn't fit on the previous page. Set
        self.is_finished to true, if everything fits.
        """
        margin = self.margin

        if self.font_size is not None:
            font_size = self.font_size
        else:
            font_size = painter.window().height() // 60
        font = QFont('NotoSansCJK')
        font.setPixelSize(font_size)
        title_font = QFont(font)
        title_font.setPixelSize(font_size*2)
        window_width = painter.window().width()
        window_height = painter.window().height()
        header_rect = QRectF(margin, margin,
                             window_width - 2*margin,
                             window_height - 2*margin)

        while not self.is_finished:
            puzzle = self.puzzles[self.puzzle_index]
            painter.setFont(font)

            if self.across_index == 0 and self.down_index == 0:
                self.draw_header(title_font, font, header_rect, painter)

            left_rect = QRectF(header_rect)
            left_rect.setWidth(left_rect.width() / 2)
            right_rect = left_rect.translated(left_rect.width(), 0)
            for section_rect in (left_rect, right_rect):
                if self.across_index == 0:
                    self.draw_text(left_rect, 'Across', painter, is_bold=True)
                clue_count = self.draw_clues(
                    painter,
                    puzzle.across_clues[self.across_index:],
                    section_rect)
                self.across_index += clue_count
                if self.across_index == len(puzzle.across_clues):
                    backup_rect = QRectF(section_rect)
                    if self.down_index == 0:
                        self.draw_text(section_rect,
                                       'Down',
                                       painter,
                                       is_dry_run=True,
                                       is_bold=True)
                    clue_count = self.draw_clues(
                        painter,
                        puzzle.down_clues[self.down_index:],
                        section_rect)
                    if clue_count and self.down_index == 0:
                        self.draw_text(backup_rect,
                                       'Down',
                                       painter,
                                       is_bold=True)
                    self.down_index += clue_count

            if self.across_index < len(puzzle.across_clues):
                return
            if self.down_index < len(puzzle.down_clues):
                return
            self.puzzle_index += 1
            self.across_index = self.down_index = 0
            return

    def draw_header(self,
                    title_font: QFont,
                    font: QFont,
                    header_rect: QRectF,
                    painter: QPainter,
                    is_dry_run: bool = False):
        if self.intro_text and self.puzzle_index == 0:
            self.draw_text(header_rect,
                           self.intro_text,
                           painter,
                           is_dry_run=is_dry_run)
        if self.footer_text and self.puzzle_index == 0:
            rect = QRectF(header_rect)
            footer_height = self.find_text_height(self.footer_text,
                                                  painter,
                                                  rect.width())
            rect.setTop(rect.bottom() - footer_height)
            header_rect.setBottom(rect.top())
            self.draw_text(rect,
                           self.footer_text,
                           painter,
                           is_centred=True,
                           is_dry_run=is_dry_run)
        painter.setFont(title_font)
        puzzle = self.puzzles[self.puzzle_index]
        painter.setFont(font)
        line_height = self.find_text_height('X', painter)
        painter.setFont(title_font)
        self.draw_text(header_rect,
                       puzzle.title,
                       painter,
                       is_centred=True,
                       background=self.background,
                       is_dry_run=is_dry_run)
        painter.setFont(font)
        self.draw_text(header_rect,
                       puzzle.build_hints(),
                       painter,
                       is_dry_run=is_dry_run)
        old_pen = painter.pen()
        pen = QPen(old_pen)
        pen.setWidth(font.pixelSize()//10)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        if not is_dry_run:
            y = round(header_rect.top() + line_height / 2)
            painter.drawLine(header_rect.left(), y, header_rect.right(), y)
        header_rect.adjust(0, line_height, 0, 0)
        painter.setPen(old_pen)

    @staticmethod
    def find_text_width(text: str, painter: QPainter) -> float:
        metrics = QFontMetricsF(painter.font())
        return metrics.horizontalAdvance(text)

    @staticmethod
    def find_text_height(text: str, painter: QPainter, width=0) -> float:
        metrics = QFontMetricsF(painter.font())
        if not width:
            width = painter.window().width()
        rect = metrics.boundingRect(QRectF(0, 0, width, 0),
                                    int(Qt.TextWordWrap),
                                    text)
        return rect.height()

    def draw_clues(self,
                   painter: QPainter,
                   clues: typing.List[Clue],
                   bounds: QRectF = None,
                   is_dry_run: bool = False) -> int:
        """ Draw clues within a rectangle.

        Returns the number of clues displayed, and sets the top of bounds to
        be the next available space.
        """
        if not clues:
            return 0
        if bounds is None:
            bounds = painter.window()
        max_clue = max(clue.number for clue in clues)
        first_clue = clues[0]
        if first_clue.suit is None:
            suit_display = ''
        else:
            suit_display = Square.SUIT_DISPLAYS['H'].filled

        puzzle = self.puzzles[self.puzzle_index]
        face_color = puzzle.face_colour
        metrics = QFontMetricsF(painter.font())
        space_width = metrics.horizontalAdvance(' ')
        align_right = int(Qt.AlignRight)
        number_width = self.find_text_width(
            f'{max_clue}{suit_display}.',
            painter)
        clue_rect = bounds.adjusted(number_width + space_width, 0, 0, 0)
        number_rect = bounds.adjusted(
            0, 0,
            number_width - bounds.width(), 0)
        clue_count = 0
        number_entries = []  # [(rect, text)]
        for clue in clues:
            temp_clue_rect = QRectF(clue_rect)
            self.draw_text(clue_rect,
                           clue.format_text(),
                           painter,
                           is_dry_run=True)
            if clue_rect.top() > clue_rect.bottom():
                break
            rect = QRectF(number_rect)
            rect.setTop(temp_clue_rect.top())

            if not is_dry_run:
                number_entries.append((rect, f'{clue.format_number()}.'))
                self.draw_text(temp_clue_rect, clue.format_text(), painter)
            bounds.setTop(clue_rect.top())
            clue_count += 1
        if number_entries:
            rect = QRectF(number_entries[0][0])
            rect.setBottom(bounds.top())
            draw_gradient_rect(painter,
                               face_color,
                               rect.left()-space_width, rect.top(),
                               rect.width()+2*space_width, rect.height(),
                               space_width*2)
            for rect, text in number_entries:
                painter.drawText(rect, align_right, text)
        return clue_count

    @staticmethod
    def draw_text(rect: QRectF,
                  text: str,
                  painter: QPainter,
                  is_centred: bool = False,
                  is_dry_run: bool = False,
                  is_aligned_right: bool = False,
                  is_bold: bool = False,
                  background: QColor = None):
        font = painter.font()
        if is_bold:
            bold_font = QFont(font)
            bold_font.setBold(is_bold)
            painter.setFont(bold_font)
        old_pen = painter.pen()
        pen = QPen(old_pen)
        pen.setWidth(font.pixelSize() // 20)
        pen.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen)
        metrics = QFontMetricsF(font)
        flags = int(Qt.TextWordWrap)
        if is_centred:
            flags = flags | Qt.AlignHCenter
        if is_aligned_right:
            flags = flags | Qt.AlignRight
        if background is None or background.alpha() == 0:
            target_rect = rect
            padding = 0
        else:
            padding = font.pixelSize() // 10
            target_rect = rect.adjusted(padding, padding, -padding, -padding)
        bounding_rect = metrics.boundingRect(target_rect, flags, text)
        if padding and not is_dry_run:
            background_rect = bounding_rect.adjusted(-padding, -padding,
                                                     padding, padding)
            painter.fillRect(background_rect, background)
            painter.drawRect(background_rect)
        height = bounding_rect.height()
        if not is_dry_run:
            painter.drawText(target_rect, flags, text)
        rect.adjust(0, math.ceil(height + metrics.leading() + 2*padding), 0, 0)
        painter.setPen(old_pen)
        painter.setFont(font)
