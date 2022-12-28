from dataclasses import dataclass

from four_letter_blocks.square import Square


@dataclass
class Clue:
    text: str
    number: int | None = None
    suit: str | None = None
    text_with_reference: str | None = None

    def format(self):
        return f'{self.format_number()}. {self.format_text()}'

    def format_text(self):
        return self.text_with_reference or self.text

    def format_number(self):
        suit_display = Square.SUIT_DISPLAYS[self.suit]
        return f'{self.number}{suit_display.display}'
