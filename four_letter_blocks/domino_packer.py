import string
import typing

from four_letter_blocks.problem_solver import ProblemSolver, SolverAlgorithm

Coordinate = typing.Tuple[int, int]


class DominoPacker:
    def __init__(self,
                 grid_text: str,
                 horizontal_dominoes: typing.Sequence[str] = (),
                 vertical_dominoes: typing.Sequence[str] = ()) -> None:
        self.lines = grid_text.splitlines()
        self.horizontal_dominoes = horizontal_dominoes
        self.vertical_dominoes = vertical_dominoes
        self.size = len(self.lines)
        self.used_options: set[str] = set()
        self.display_text: list[list[str]] = []
        for y, line in enumerate(self.lines):
            if y > 0:
                self.display_text.append([' ']*(self.size*2-1))
            new_line: list[str] = []
            for x, c in enumerate(line):
                if x > 0:
                    new_line.append(' ')
                new_line.append(c)
            self.display_text.append(new_line)

    def add_domino(self, coords1: Coordinate, coords2: Coordinate) -> None:
        x1, y1 = coords1
        x2, y2 = coords2
        if x1 == x2:
            divider = '-'
        else:
            divider = '|'
        x = (x1*2 + x2*2) // 2
        y = (y1*2 + y2*2) // 2
        self.display_text[y][x] = divider

    def display(self) -> str:
        return '\n'.join(''.join(line).rstrip() for line in self.display_text)

    def fill(self) -> bool:
        solver = ProblemSolver(SolverAlgorithm.MULTIPLES)
        for y in range(self.size):
            for x in range(self.size):
                if self.lines[y][x] != '#':
                    solver.primary(f's{x}_{y}')
        for domino_index, domino in enumerate(self.horizontal_dominoes):
            domino_name = f'h{domino}{domino_index}'
            solver.primary(domino_name, 0, 1)
            for x in range(self.size-1):
                for y in range(self.size):
                    if self.lines[y][x] + self.lines[y][x+1] == domino:
                        solver.add(domino_name)
                        solver.add(f's{x}_{y}')
                        solver.add(f's{x+1}_{y}')
                        solver.add(0)
        for domino_index, domino in enumerate(self.vertical_dominoes):
            domino_name = f'v{domino}{domino_index}'
            solver.primary(domino_name, 0, 1)
            for x in range(self.size):
                for y in range(self.size-1):
                    if self.lines[y][x] + self.lines[y+1][x] == domino:
                        solver.add(domino_name)
                        solver.add(f's{x}_{y}')
                        solver.add(f's{x}_{y+1}')
                        solver.add(0)
        for c in string.ascii_uppercase:
            mono_name = f'o{c}'
            solver.primary(mono_name, 0, 1)
            for x in range(self.size):
                for y in range(self.size):
                    if self.lines[y][x] == c:
                        solver.add(mono_name)
                        solver.add(f's{x}_{y}')
                        solver.add(0)
        # print(solver.format_problem())
        option_sets = solver.solve()
        if option_sets is None:
            return False

        for option_set in option_sets:
            self.used_options.update(option
                                     for option in option_set
                                     if option[0] in 'hvo')
            space_options = [option
                             for option in option_set
                             if option[0] == 's']
            if len(space_options) != 2:
                continue
            text_coordinates = [option[1:].split('_')
                                for option in space_options]
            coordinates = [(int(x_text), int(y_text))
                           for x_text, y_text in text_coordinates]
            coords1, coords2 = coordinates
            self.add_domino(coords1, coords2)
        return True
