from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter, QFont, Qt

from four_letter_blocks.puzzle import Puzzle


class CluePainter:
    def __init__(self, *puzzles: Puzzle, font_size: int = None, margin: int = 0):
        self.puzzles = puzzles
        self.font_size = font_size
        self.margin = margin
        self.puzzle_index = 0

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
        title_font.setPixelSize(font_size * 2)
        painter.setFont(title_font)
        metrics = painter.fontMetrics()

        puzzle = self.puzzles[self.puzzle_index]
        window_width = painter.window().width()
        window_height = painter.window().height()
        centred = int(Qt.AlignHCenter)
        word_wrap = int(Qt.TextWordWrap)
        title_start = margin
        title_rect = QRect(margin, title_start,
                           window_width-2*margin, window_height)
        rect = metrics.boundingRect(title_rect, centred, puzzle.title)
        painter.drawText(title_rect, centred, puzzle.title)
        hint_start = rect.bottom()

        painter.setFont(font)
        metrics = painter.fontMetrics()

        hints = puzzle.build_hints()
        hints_rect = QRect(margin, hint_start,
                           window_width - 2*margin, window_height)
        rect = metrics.boundingRect(hints_rect, word_wrap, hints)
        painter.drawText(hints_rect, word_wrap, hints)
        line_start = rect.bottom() + font_size//2
        painter.drawLine(margin, line_start, window_width - margin, line_start)
        header_start = rect.bottom() + font_size

        left_header_rect = QRect(margin, header_start,
                                 window_width//2 - margin, window_height)
        right_header_rect = QRect(window_width//2, header_start,
                                  window_width//2 - margin, window_height)
        painter.drawText(left_header_rect, 0, 'Across')
        painter.drawText(right_header_rect, 0, 'Down')
        clue_start = header_start + metrics.lineSpacing()

        max_clue = max(clue.number for clue in puzzle.all_clues.values())
        number_width = metrics.horizontalAdvance(f'{max_clue}.')
        left_number_rect = QRect(
            margin, clue_start,
            number_width, window_height - margin - clue_start)
        left_clue_rect = QRect(
            margin + number_width, clue_start,
            window_width//2 - margin - number_width, left_number_rect.height())
        right_number_rect = QRect(window_width//2, clue_start,
                                  number_width, left_number_rect.height())
        right_clue_rect = QRect(window_width//2 + number_width, clue_start,
                                left_clue_rect.width(), left_number_rect.height())
        draw_clues(painter,
                   puzzle.across_clues,
                   left_number_rect,
                   left_clue_rect)
        draw_clues(painter,
                   puzzle.down_clues,
                   right_number_rect,
                   right_clue_rect)


def draw_clues(painter, clues, next_number_rect, next_clue_rect):
    metrics = painter.fontMetrics()
    align_right = int(Qt.AlignRight)
    word_wrap = int(Qt.TextWordWrap)
    bottom = next_clue_rect.bottom()
    for clue in clues:
        rect = metrics.boundingRect(next_clue_rect, word_wrap, clue.text)
        if rect.bottom() > bottom:
            return
        painter.drawText(next_number_rect, align_right, f'{clue.number}.')
        painter.drawText(next_clue_rect, word_wrap, clue.text)
        next_number_rect = next_number_rect.translated(0, rect.height())
        next_clue_rect = next_clue_rect.translated(0, rect.height())
