from PySide6.QtCore import QRect
from PySide6.QtGui import QPainter, QFont, Qt

from four_letter_blocks.puzzle import Puzzle


class CluePainter:
    def __init__(self, *puzzles: Puzzle,
                 font_size: float = None,
                 margin: int = 0):
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
        title_font.setPixelSize(font_size*2)
        painter.setFont(title_font)

        puzzle = self.puzzles[self.puzzle_index]
        window_width = painter.window().width()
        window_height = painter.window().height()
        centred = int(Qt.AlignHCenter)
        word_wrap = int(Qt.TextWordWrap)
        title_start = margin
        title_rect = QRect(margin, title_start,
                           window_width-2*margin, window_height)
        hint_start = title_start + self.find_text_height(puzzle.title,
                                                         painter,
                                                         title_rect.width())
        painter.drawText(title_rect, centred, puzzle.title)

        painter.setFont(font)
        hints = puzzle.build_hints()
        hints_rect = QRect(margin, hint_start,
                           window_width - 2*margin, window_height)
        divider_start = hint_start + self.find_text_height(hints,
                                                           painter,
                                                           hints_rect.width())
        line_height = self.find_text_height('X', painter)
        painter.drawText(hints_rect, word_wrap, hints)
        painter.drawLine(margin, divider_start + line_height//2,
                         window_width - margin, divider_start + line_height//2)
        header_start = divider_start + line_height

        left_header_rect = QRect(margin, header_start,
                                 window_width//2 - margin, window_height)
        right_header_rect = QRect(window_width//2, header_start,
                                  window_width//2 - margin, window_height)
        painter.drawText(left_header_rect, 0, 'Across')
        painter.drawText(right_header_rect, 0, 'Down')
        clue_start = header_start + line_height

        max_clue = max(clue.number for clue in puzzle.all_clues.values())
        number_width = self.find_text_width(f'{max_clue}. ', painter)
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


def draw_clues(painter, clues, next_number_rect, next_clue_rect):
    metrics = painter.fontMetrics()
    align_right = int(Qt.AlignRight)
    word_wrap = int(Qt.TextWordWrap)
    bottom = next_clue_rect.bottom()
    for clue in clues:
        rect = metrics.boundingRect(next_clue_rect, word_wrap, clue.text)
        if rect.bottom() > bottom:
            return
        painter.drawText(next_number_rect, align_right, f'{clue.number}. ')
        painter.drawText(next_clue_rect, word_wrap, clue.text)
        next_number_rect = next_number_rect.translated(0, rect.height())
        next_clue_rect = next_clue_rect.translated(0, rect.height())
