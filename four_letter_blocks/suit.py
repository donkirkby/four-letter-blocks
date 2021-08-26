from dataclasses import dataclass


@dataclass
class Suit:
    display: str
    filled: str = None

    def __post_init__(self):
        if self.filled is None:
            self.filled = self.display
