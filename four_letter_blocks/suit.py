from dataclasses import dataclass


@dataclass
class Suit:
    display: str
    filled: str = ''

    def __post_init__(self):
        if self.filled == '':
            self.filled = self.display
