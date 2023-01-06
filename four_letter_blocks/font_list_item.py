from PySide6.QtGui import QFont
from PySide6.QtWidgets import QListWidgetItem


class FontListItem(QListWidgetItem):
    def __init__(self, font: QFont):
        label = "ABC QRS - " + font.family()
        if font.weight() == QFont.Weight.Bold:
            label += " Bold"
        if font.style() == QFont.Style.StyleItalic:
            label += " Italic"
        super().__init__(label)
        self.setFont(font)
