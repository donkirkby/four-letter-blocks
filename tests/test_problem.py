from pathlib import Path
from textwrap import dedent

import pytest

from four_letter_blocks.problem import SolverAlgorithm, Problem


def test_primary():
    problem = Problem(SolverAlgorithm.EXACT)

    problem.primary('a')

    problem_dlx = problem.format_problem()

    expected_dlx = dedent('''\
        a
        ''')

    assert expected_dlx == problem_dlx


def test_add():
    problem = Problem(SolverAlgorithm.EXACT)

    problem.primary('a')
    problem.primary('b')

    problem.add('a')
    a_option_num = problem.add(0)

    ignored_option_num = problem.add('b')
    b_option_num = problem.add(0)

    problem_dlx = problem.format_problem()

    expected_dlx = dedent('''\
        a b
        a #
        b #
        ''').replace('#', '')

    assert expected_dlx == problem_dlx
    assert a_option_num == 1
    assert ignored_option_num == 0
    assert b_option_num == 2


def test_multiples():
    problem = Problem(SolverAlgorithm.MULTIPLES)

    problem.primary('a', 2, 3)
    problem.primary('b')

    problem.add('a')
    problem.add(0)

    problem.add('b')
    problem.add(0)

    problem.add('a')
    problem.add('b')
    problem.add(0)

    problem_dlx = problem.format_problem()

    expected_dlx = dedent('''\
        a:2;3 b
        a #
        b #
        a b #
        ''').replace('#', '')

    assert expected_dlx == problem_dlx


def test_shuffle():
    problem = Problem(SolverAlgorithm.EXACT)

    problem.primary('a')
    problem.primary('b')

    problem.add('a')
    problem.add(0)

    problem.add('b')
    problem.add(0)

    all_dlx_texts = set()

    for _ in range(100):
        problem_dlx = problem.format_problem()
        all_dlx_texts.add(problem_dlx)
        problem.shuffle()

    all_expected_dlx_texts = {dedent('''\
                                a b
                                a #
                                b #
                                ''').replace('#', ''),
                              dedent('''\
                                a b
                                b #
                                a #
                                ''').replace('#', ''),
                              dedent('''\
                                b a
                                a #
                                b #
                                ''').replace('#', ''),
                              dedent('''\
                                b a
                                b #
                                a #
                                ''').replace('#', '')
                              }

    assert all_expected_dlx_texts == all_dlx_texts

def test_solve():
    problem = Problem(SolverAlgorithm.EXACT)

    problem.primary('a')
    problem.primary('b')

    problem.add('a')
    problem.add(0)

    problem.add('b')
    problem.add(0)

    selected_options = problem.solve()

    assert selected_options == [('a',), ('b',)]


def test_solve_multiples():
    problem = Problem(SolverAlgorithm.MULTIPLES)

    problem.primary('a', 2, 3)
    problem.primary('b')

    problem.add('a')
    problem.add(0)

    problem.add('b')
    problem.add(0)

    problem.add('a')
    problem.add('b')
    problem.add(0)

    selected_options = problem.solve()

    expected_options = [('a',), ('a', 'b')]
    assert selected_options == expected_options

def test_solve_fails():
    problem = Problem(SolverAlgorithm.EXACT)

    problem.primary('a')
    problem.primary('b')

    problem.add('a')
    problem.add(0)

    selected_options = problem.solve()

    assert selected_options is None

def test_solve_with_timeout():
    problem = Problem(SolverAlgorithm.EXACT)

    problem.primary('a')
    problem.primary('b')

    problem.add('a')
    problem.add(0)

    problem.add('b')
    problem.add(0)

    selected_options = problem.solve(timeout=1.0)

    assert selected_options == [('a',), ('b',)]

def test_solve_fails_with_timeout():
    problem = Problem(SolverAlgorithm.EXACT)

    problem.primary('a')
    problem.primary('b')

    problem.add('a')
    problem.add(0)

    selected_options = problem.solve(timeout=1.0)

    assert selected_options is None


def test_solve_slow_problem_with_timeout():
    problem_path = Path(__file__).with_name('slow_problem.dlx')
    problem_text = problem_path.read_text()
    problem_lines = problem_text.splitlines()
    items = problem_lines[0].split()
    problem = Problem(SolverAlgorithm.EXACT)
    for item in items:
        problem.primary(item)
    for option in problem_lines[1:]:
        option_items = option.split()
        for item in option_items:
            problem.add(item)
        problem.add(0)

    selected_options = problem.solve(timeout=60.0)  # Solvable, but slow.

    assert selected_options is not None
    assert len(selected_options) == 24

    with pytest.raises(TimeoutError):
        problem.solve(timeout=1.0)


