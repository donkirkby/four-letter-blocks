from PySide6.QtCore import Signal
from PySide6.QtGui import QFocusEvent
from PySide6.QtWidgets import QPlainTextEdit


class FocusedPlainTextEdit(QPlainTextEdit):
    focused = Signal()

    def focusInEvent(self, e: QFocusEvent):
        super().focusInEvent(e)
        # noinspection PyUnresolvedReferences
        self.focused.emit()
