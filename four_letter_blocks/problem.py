from enum import Enum, auto
from multiprocessing import Process, Queue
from random import shuffle
from tempfile import NamedTemporaryFile

from miniexact import miniexacts_x, miniexacts_m

class SolverAlgorithm(Enum):
    EXACT = auto()
    MULTIPLES = auto()

class Problem:
    def __init__(self, algorithm: SolverAlgorithm) -> None:
        self.algorithm = algorithm
        self.items: list[tuple[str, int, int]] = []
        self.current_option: list[str] = []
        self.options: list[tuple[str, ...]] = []
        self.queue: Queue[None | list[tuple[str, ...]]] | None = None

    def create_solver(self):
        option_index = {}
        if self.algorithm == SolverAlgorithm.EXACT:
            solver = miniexacts_x()
        else:
            solver = miniexacts_m()
        for name, u, v in self.items:
            solver.primary(name, u, v)
        for option in self.options:
            for item in option:
                solver.add(item)
            option_num = solver.add(0)
            option_index[option_num] = option
        return solver, option_index

    def primary(self, name: str, u: int=1, v: int=1):
        self.items.append((name, u, v))

    def add(self, name: str | int) -> int:
        if isinstance(name, str):
            self.current_option.append(name)
            return 0
        else:
            assert name == 0
            self.options.append(tuple(self.current_option))
            self.current_option.clear()
            return len(self.options)

    def format_problem(self) -> str:
        solver, _ = self.create_solver()

        with NamedTemporaryFile() as tmp:
            solver.write_to_dlx(tmp.name)
            tmp.seek(0)
            return tmp.read().decode()

    def shuffle(self) -> None:
        shuffle(self.items)
        shuffle(self.options)

    def solve(self, timeout: float = 0) -> list[tuple[str, ...]] | None:
        """ Solve the problem.

        :param timeout: Timeout in seconds, before the worker process should be
        killed. Defaults to 0, meaning no timeout, and run in the current
        process.
        :return: a list of selected options, each of which is a tuple of item
        names. If the problem has no solution, return None.
        """
        if timeout > 0:
            self.queue = Queue()
            worker = Process(target=self.solve, daemon=True)
            worker.start()
            worker.join(timeout)
            if worker.exitcode is None:
                worker.kill()
                self.queue = None
                raise TimeoutError(f'Solver timed out after {timeout} seconds.')
            assert self.queue is not None
            selected_options = self.queue.get_nowait()
            self.queue = None
            return selected_options

        solver, option_index = self.create_solver()
        status = solver.solve()

        if status == 20:
            selected_options = None
        else:
            selected_indexes = solver.selected_options()
            selected_options = [option_index[i] for i in selected_indexes]
        if self.queue is not None:
            self.queue.put_nowait(selected_options)
        return selected_options
