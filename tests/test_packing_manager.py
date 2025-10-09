from multiprocessing import Queue
from textwrap import dedent

from four_letter_blocks.packing_manager import PackingManager, PackingRequest, PackingScenario, PackingResponse


def test_pack_puzzle():
    start_text = dedent("""\
        #.....#
        ...#...
        .......
        .#.#.#.
        .......
        ...#...
        #.....#""")
    expected_filled = dedent("""\
        #AAABB#
        GGA#BBC
        HGGFFCC
        H#J#F#C
        HHJJFDD
        IIJ#EDD
        #IIEEE#""")
    request = PackingRequest(scenario=PackingScenario.SINGLE_PUZZLE,
                             target_texts=(start_text,))
    expected_response = PackingResponse(scenario=request.scenario,
                                        target_texts=(expected_filled,))
    queue = Queue()
    manager = PackingManager(request, queue)

    manager.pack()

    response: PackingResponse = queue.get(block=True, timeout=0.1)
    assert response == expected_response


def test_pack_pair():
    # Why is this solution for demo d not showing up in the log?
    start_texts = (# Greetings: J2, S4, T4
                   dedent("""\
                    #.....#
                    ...#...
                    .......
                    .#.#.#.
                    .......
                    ...#...
                    #.....#"""),
                   # demo d: L0: 1, L2: 1, T0: 1, T1: 1, T2: 1, T3: 1, Z0: 4
                   # demo d: L2, Z4, T4
                   dedent("""\
                    ....#.#
                    .......
                    ....#.#
                    ...#...
                    #.#....
                    .......
                    #.#...."""))
    expected_displays = (dedent("""\
                            #AABBB#
                            AAC#BDD
                            EECCDDF
                            E#C#G#F
                            EHHGGFF
                            HHI#GJJ
                            #IIIJJ#"""),
                         dedent("""\
                            AADD#G#
                            FAADDGG
                            FBBB#G#
                            FFB#IEE
                            #C#IIIE
                            CCHHJJE
                            #C#HHJJ"""))
    request = PackingRequest(scenario=PackingScenario.PUZZLE_PAIR,
                             target_texts=start_texts)
    expected_response = PackingResponse(scenario=request.scenario,
                                        target_texts=expected_displays,
                                        sides=((0, ), (1, )))
    queue = Queue()
    manager = PackingManager(request, queue)

    manager.pack()

    response: PackingResponse = queue.get(block=True, timeout=100)
    assert response == expected_response
