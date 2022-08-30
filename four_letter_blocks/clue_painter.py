import typing

from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter, QFont, Qt

from four_letter_blocks.clue import Clue
from four_letter_blocks.puzzle import Puzzle
from four_letter_blocks.square import Square


class CluePainter:
    def __init__(self, *puzzles: Puzzle,
                 font_size: float = None,
                 margin: int = 0,
                 intro_text: str = '',
                 footer_text: str = ''):
        self.puzzles = puzzles
        self.font_size = font_size
        self.margin = margin
        self.puzzle_index = self.across_index = self.down_index = 0
        self.intro_text = intro_text
        self.footer_text = footer_text

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
        font = painter.font()
        font.setPixelSize(font_size)
        title_font = QFont(font)
        title_font.setPixelSize(font_size*2)
        title_start = margin

        while not self.is_finished:
            puzzle = self.puzzles[self.puzzle_index]

            window_width = painter.window().width()
            window_height = painter.window().height()
            painter.setFont(font)
            max_clue = max(clue.number for clue in puzzle.all_clues.values())
            first_clue = puzzle.across_clues[0]
            if first_clue.suit is None:
                suit_display = ''
            else:
                suit_display = Square.SUIT_DISPLAYS['H'].filled
            number_width = self.find_text_width(
                f'{max_clue}{suit_display}. ',
                painter)
            clue_width = window_width//2 - margin - number_width

            bottom = window_height - margin
            if self.across_index == 0 and self.down_index == 0:
                if self.intro_text and self.puzzle_index == 0:
                    rect = QRect(margin, title_start,
                                 window_width - 2*margin, window_height)
                    title_start += self.find_text_height(self.intro_text,
                                                         painter,
                                                         rect.width())
                    painter.drawText(rect, int(Qt.TextWordWrap), self.intro_text)
                if self.footer_text and self.puzzle_index == 0:
                    rect = QRect(margin, 0,
                                 window_width - 2*margin, window_height)
                    footer_height = self.find_text_height(self.footer_text,
                                                          painter,
                                                          rect.width())
                    bottom -= footer_height
                    rect.moveTop(bottom)
                    painter.drawText(rect,
                                     int(Qt.TextWordWrap | Qt.AlignHCenter),
                                     self.footer_text)

                clue_start = self.draw_header(title_font,
                                              font,
                                              margin,
                                              title_start,
                                              clue_width,
                                              painter)
                if clue_start <= title_start:
                    return
            else:
                clue_start = margin
                painter.setFont(font)

            left_number_rect = QRect(
                margin, clue_start,
                number_width, bottom - clue_start)
            left_clue_rect = QRect(
                margin + number_width, clue_start,
                window_width//2 - margin - number_width, left_number_rect.height())
            right_number_rect = QRect(window_width//2, clue_start,
                                      number_width, left_number_rect.height())
            right_clue_rect = QRect(window_width//2 + number_width, clue_start,
                                    left_clue_rect.width(), left_number_rect.height())
            left_clue_count, left_bottom = self.draw_clues(
                painter,
                puzzle.across_clues[self.across_index:],
                left_number_rect,
                left_clue_rect)
            right_clue_count, right_bottom = self.draw_clues(
                painter,
                puzzle.down_clues[self.down_index:],
                right_number_rect,
                right_clue_rect)
            self.across_index += left_clue_count
            self.down_index += right_clue_count

            if self.across_index < len(puzzle.across_clues):
                return
            if self.down_index < len(puzzle.down_clues):
                return
            self.puzzle_index += 1
            self.across_index = self.down_index = 0
            return

    def draw_header(self,
                    title_font,
                    font,
                    margin,
                    title_start,
                    clue_width,
                    painter):
        painter.setFont(title_font)
        puzzle = self.puzzles[self.puzzle_index]
        window_width = painter.window().width()
        window_height = painter.window().height()
        centred = int(Qt.AlignHCenter | Qt.TextWordWrap)
        word_wrap = int(Qt.TextWordWrap)
        title_rect = QRect(margin, title_start,
                           window_width - 2 * margin, window_height)
        hint_start = title_start + self.find_text_height(puzzle.title,
                                                         painter,
                                                         title_rect.width())
        painter.setFont(font)
        hints = puzzle.build_hints()
        hints_rect = QRect(margin, hint_start,
                           window_width - 2 * margin, window_height)
        divider_start = hint_start + self.find_text_height(hints,
                                                           painter,
                                                           hints_rect.width())
        line_height = self.find_text_height('X', painter)
        header_start = divider_start + line_height
        left_header_rect = QRect(margin, header_start,
                                 window_width // 2 - margin, window_height)
        right_header_rect = QRect(window_width // 2, header_start,
                                  window_width // 2 - margin, window_height)
        clue_start = header_start + line_height
        across_height = self.find_text_height(
            puzzle.across_clues[0].format_text(),
            painter,
            clue_width)
        down_height = self.find_text_height(
            puzzle.down_clues[0].format_text(),
            painter,
            clue_width)
        clue_bottom = clue_start + max(across_height, down_height)
        if clue_bottom > window_height - margin:
            return title_start

        painter.setFont(title_font)
        painter.drawText(title_rect, centred, puzzle.title)
        painter.setFont(font)
        painter.drawText(hints_rect, word_wrap, hints)
        painter.drawLine(margin, divider_start + line_height // 2,
                         window_width - margin, divider_start + line_height // 2)
        painter.drawText(left_header_rect, 0, 'Across')
        painter.drawText(right_header_rect, 0, 'Down')
        return clue_start

    @staticmethod
    def find_text_width(text: str, painter: QPainter) -> int:
        metrics = painter.fontMetrics()
        return metrics.horizontalAdvance(text)

    @staticmethod
    def find_text_height(text: str, painter: QPainter, width=0) -> int:
        metrics = painter.fontMetrics()
        if not width:
            width = painter.window().width()
        rect = metrics.boundingRect(0, 0,
                                    width, 0,
                                    int(Qt.TextWordWrap),
                                    text)
        return rect.height()

    def draw_clues(self,
                   painter: QPainter,
                   clues: typing.List[Clue],
                   next_number_rect: QRect,
                   next_clue_rect: QRect) -> typing.Tuple[int, int]:
        puzzle = self.puzzles[self.puzzle_index]
        face_color = puzzle.face_colour
        metrics = painter.fontMetrics()
        space_width = metrics.horizontalAdvance(' ')
        align_right = int(Qt.AlignRight)
        word_wrap = int(Qt.TextWordWrap)
        page_bottom = next_clue_rect.bottom()
        clue_count = 0
        for clue in clues:
            rect = metrics.boundingRect(next_clue_rect,
                                        word_wrap,
                                        clue.format_text())
            if rect.bottom() > page_bottom:
                break
            rect.setLeft(next_number_rect.left())
            rect.setRight(next_number_rect.right() - space_width//2)
            painter.fillRect(rect, face_color)
            painter.drawText(next_number_rect, align_right, f'{clue.format_number()}. ')
            painter.drawText(next_clue_rect, word_wrap, clue.format_text())
            next_number_rect = next_number_rect.translated(0, rect.height())
            next_clue_rect = next_clue_rect.translated(0, rect.height())
            clue_count += 1
        return clue_count, next_clue_rect.top()
