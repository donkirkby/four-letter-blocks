from enum import Enum, auto
from multiprocessing import Process, Queue
from random import shuffle
from tempfile import NamedTemporaryFile

from miniexact import miniexacts_x, miniexacts_m

class SolverAlgorithm(Enum):
    EXACT = auto()
    MULTIPLES = auto()

ProblemOption = tuple[str, ...]
OptionList = list[tuple[str, ...]]

class ProblemSolver:
    """ Holds the items and options for a problem, and solves the problem. """
    def __init__(self, algorithm: SolverAlgorithm) -> None:
        self.algorithm = algorithm
        self.items: list[tuple[str, int, int]] = []
        self.current_option: list[str] = []
        self.options: OptionList = []
        self.queue: Queue[None | OptionList] | None = None
        self.worker: Process | None = None

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

    def add(self, name: str | int) -> ProblemOption | None:
        """ Add a new primary item to the current option.

        :param name: the name of the primary item, or 0 to end the option.
        :return: a tuple of item names, when you end the option, otherwise None.
        """
        if isinstance(name, str):
            self.current_option.append(name)
            return None
        else:
            assert name == 0
            new_option = tuple(self.current_option)
            self.options.append(new_option)
            self.current_option.clear()
            return new_option

    def format_problem(self) -> str:
        solver, _ = self.create_solver()

        with NamedTemporaryFile() as tmp:
            solver.write_to_dlx(tmp.name)
            tmp.seek(0)
            return tmp.read().decode()

    def shuffle(self) -> None:
        shuffle(self.items)
        shuffle(self.options)

    def solve(self, timeout: float | None = None) -> OptionList | None:
        """ Solve the problem.

        :param timeout: Timeout in seconds, before the worker process should be
        killed. Defaults to None, meaning no timeout, and run in the current
        process. If you pass a negative number, then it will run in a worker
        process with an infinite timeout.
        :return: a list of selected options, each of which is a tuple of item
        names. If the problem has no solution, return None.
        """
        if not self.options:
            return None

        if timeout is not None:
            if timeout < 0:
                worker_timeout = None
            else:
                worker_timeout = timeout
            self.queue = Queue()
            worker = Process(target=self.solve, daemon=True)
            worker.start()
            self.worker = worker
            worker.join(worker_timeout)
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

    def cancel(self) -> None:
        if self.worker is None:
            return

        self.worker.kill()

    def copy(self) -> 'ProblemSolver':
        other = ProblemSolver(self.algorithm)
        other.items = self.items[:]
        other.options = self.options[:]
        return other
