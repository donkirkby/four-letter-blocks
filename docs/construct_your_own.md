---
title: Construct Your Own
subtitle: Step by step
---

To construct your own puzzle, you have to construct the crossword puzzle, split
it up into blocks of four letters, and then publish it.

### Constructing the Crossword
There are a few articles around on how to construct a crossword puzzle, start
with the series by the [New York Times]. You could use graph paper and a pencil,
but I strongly recommend [QXW builder] and its [manual]. It's very helpful,
because it shows you which squares you should fill in first, because they have
the fewest feasible letters. [Phil grid builder] makes a good companion, and it
has the advantage that it runs in a web browser.

For the black squares, all the usual style guides apply: rotational symmetry, no
two-letter words, and so on. The only additional guide is that you should have a
multiple of four letters. In squares of an odd number, the standard, that means
that you have to make the central square black. It will still work if you don't
use a multiple of four squares, you'll just have to make the blocks different
sizes.

The grid size should be between 7x7 and 11x11. Anything bigger than 11x11
becomes too frustrating to solve, and it takes too long to find a piece with the
right clue number.

### Installing the Software
The next step happens in the Four-Letter Blocks program, so install it with
`pip install four-letter-blocks`. If you haven't installed Python packages
before, read Brett Cannon's [quick-and-dirty guide].

Then run it with the `four_letter_blocks` command.

The default installation generates some errors about `bdist_wheel` that don't
seem to actually cause any problems. You can either ignore them, or install
`wheel` before installing Four-Letter Blocks.

    pip install wheel
    pip install four-letter-blocks
    four_letter_blocks

Known bug on Ubuntu 20.04:

> ImportError: libOpenGL.so.0: cannot open shared object file: No such file or
> directory

This is a [PySide6 bug] that is missing some dependencies. You can work around
it by installing those dependencies like this:

    sudo apt-get install freeglut3 freeglut3-dev

### Splitting Up the Grid
Start by filling in the title
and grid. Use the `#` character for black squares. As you type, the bottom of
the window will display the number of letters. If the remainder is zero, then
they will divide evenly into blocks of four. Save your progress by typing
<kbd>Ctrl</kbd>+<kbd>S</kbd>.

All the words from the grid are displayed in the list of clues, so fill in the
clues. Don't worry about clue numbers, those will be assigned after you split
up the grid and shuffle the blocks. Each line in the clues field should look
like this:

> WORD - A clue for the word

If you want one clue to refer to another, place the target word in your clue,
in all caps. The word will be replaced with its clue number.

A word of advice: make the clues easier than you think you should. Because of
the extra challenges in this type of puzzle, at least half the clues should be
very easy so the solver can make some progress. Once you've written all the
clues, print out the grid and circle the words with the hardest clues. Make
sure you don't have too many difficult words grouped together.

The last field is for splitting the grid into blocks. Use a different letter for
each block. If you have more than 26 blocks, use lower case letters as well. As
you type, the bottom of the window will show any blocks that don't have four
letters. Review the difficult words that you circled earlier. Use a combination
of easy crossing clues and longer block sections to make the difficult words
easier to solve.

When you've assigned all the blocks, choose Shuffle from the Edit menu to mix
up the order of the clue numbers.

### Publishing
You may publish your puzzle wherever you like, and you're welcome to post it
in this project's [Show and Tell] discussion. Choose Export... from the File
menu to write PDF, PNG, and markdown files for publishing. Check the PDF to make
sure all the blocks fit on one page. If not, try shuffling and exporting again.

If you are going to publish in Show and Tell, please keep the words and clue
topics light and entertaining. If you get feedback from solvers, please keep
discussions constructive and polite.

[New York Times]: https://www.nytimes.com/2018/09/14/crosswords/how-to-make-a-crossword-puzzle-the-series.html
[QXW builder]: https://www.quinapalus.com/qxw.html
[manual]: https://www.quinapalus.com/qxw-guide-20200708.pdf
[Phil grid builder]: https://www.keiranking.com/apps/phil/
[quick-and-dirty guide]: https://snarky.ca/a-quick-and-dirty-guide-on-how-to-install-packages-for-python/
[PySide6 bug]: https://bugreports.qt.io/browse/PYSIDE-1547
[Show and Tell]: https://github.com/donkirkby/four-letter-blocks/discussions/categories/show-and-tell