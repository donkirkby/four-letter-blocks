class ClueOverflow(Exception):
    def __init__(self, *args):
        super().__init__(*args)

    def __str__(self):
        room, clues = self.args
        return f'Only had room for {room} of {clues} clues.'
