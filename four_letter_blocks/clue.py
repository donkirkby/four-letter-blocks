from dataclasses import dataclass

from four_letter_blocks.square import Square


@dataclass
class Clue:
    text: str
    number: int = None
    suit: str = None

    def format(self):
        return f'{self.format_number()}. {self.text}'

    def format_number(self):
        suit_display = Square.SUIT_DISPLAYS.get(self.suit, '')
        return f'{self.number}{suit_display}'
