from PySide6.QtCore import Signal
from PySide6.QtGui import QDropEvent
from PySide6.QtWidgets import QListWidget


class DraggableList(QListWidget):
    dropped = Signal()

    def dropEvent(self, event: QDropEvent) -> None:
        super().dropEvent(event)
        # noinspection PyUnresolvedReferences
        self.dropped.emit()
