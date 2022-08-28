---
title: Construct Your Own
subtitle: Step by step
---

To construct your own puzzle, you have to construct the crossword puzzle, split
it up into blocks of four letters, and then publish it.

### Constructing the Crossword
There are a few articles around on how to construct a crossword puzzle, start
with the series by the [New York Times]. You could use graph paper and a pencil,
but I strongly recommend [Qxw builder] and its [manual]. It's very helpful,
because it shows you which squares you should fill in first, because they have
the fewest feasible letters. [Phil grid builder] makes a good companion, and it
has the advantage that it runs in a web browser.

If you're struggling to find theme entries, one technique is to find web pages
related to the theme, save them as text files with pandoc, lynx, or Emacs, and
then grep the text files for words or phrases of the right length. Here's a
command that looks for 11-letter words and a command that looks for 11-letter
phrases.

    egrep -oh "(^|\W)\w{11}(\W|$)" web-page.txt | sort -u | less
    egrep -oh "(^|\W)\w(\W*\w){9}\w(\W|$)" web-page.txt | sort -u | less

For the black squares, all the usual style guides apply: rotational symmetry, no
two-letter words, and so on. The only additional guide is that you should have a
multiple of four letters. In squares of an odd number, the standard, that means
that you have to make the central square black. It will still work if you don't
use a multiple of four squares, you'll just have to make the blocks different
sizes. In Qxw builder, choose Show Statistics from the Edit menu, and leave it
open. It will show you if you have any two-letter words. It also tells you the
total number of grid cells, so you can check that it's a multiple of four.

The grid size should be between 7x7 and 15x15. Anything bigger than 11x11 gets
the card suits to help solvers work on one corner at a time, and anything
bigger than 15x15 becomes too frustrating to solve. It takes too long to find
a piece with the right clue number.

I recommend you use the statistics window to check the following things when you
finish laying out the black squares, or blocks:
* total cells is a multiple of four
* no two-letter words
* no underchecked cells
* not too many overchecked cells (a few are fine to build solid areas of words,
but too many will make the grid hard to fill)

#### Advanced Construction
I found the basic features of Qxw builder were good enough for the smaller
grids, but I kept getting stuck when I tried to construct a 15x15 grid with
four theme entries. To get that to work, I read through the manual and learned
how to select lights and override dictionaries. Then I used the following steps:

1. Write a custom dictionary just with theme entries that you want to choose
from. It can include entries that are multiple words, like ANEXAMPLE. I tried to
include about twice as many entries as I needed for each length in the grid.
The more you include, the easier it will be to fill the grid.
2. Start laying out the grid in Qxw builder by adding blocks, making sure that
you include lights of the right length for your theme entries.
3. Select all the lights where you want theme entries, and override the light
properties to use the custom dictionary instead of the regular dictionary.
4. Try running autofill just to see if it's possible. You won't keep this grid,
it's just to test whether your theme entries and blocks are too hard to fill.
5. If the autofill fails, try to make things easier. You can either add more
theme entries to choose from in the custom dictionary, or you can change the
blocks so the theme lights aren't so tightly connected.
6. Once the autofill works, move the mouse to clear out the autofill hints. Then
look at the red blocks to see which cells are hardest to fill, and run autofill
a few times to see which words are possible through those cells.
7. If the autofill always produces the same grid, check that the autofill
preferences are highly randomised and prevent duplicates.
8. Pick one of the words you like from the autofill choices, and type it in.
Then go back to step 6. You can also look at the recommended letters and choose
your own word to type in. Just make sure that autofill still works.

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

All the words from the grid are displayed in the list of clues, so take a
quick scan through looking for words that are too similar. Sometimes the
autofill will suggest different spellings of the same word or singular and
plural versions of the same word, and you might not notice. Then fill in the
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

### Testing
Export the puzzle to a PNG file, and then try to solve it, assuming you don't
know the answers to the hardest clues. Check for easy clues where there are
several possible blocks to continue the word. It can be frustrating for solvers
if that happens with too many clues.

If possible, get someone who doesn't know the answers to try solving it before
you publish. You might be surprised that some clues were harder than you
expected, or they might find a problem that you didn't notice.

### Publishing
You may publish your puzzle wherever you like, and you're welcome to post it
in this project's [Show and Tell] discussion. Choose Export... from the File
menu to write PDF, PNG, and markdown files for publishing.

If you are going to publish in Show and Tell, please keep the words and clue
topics light and entertaining. If you get feedback from solvers, please keep
discussions constructive and polite.

### Puzzle Sets
If you want to publish a professional-quality set of puzzles, [Game Crafter] is
a good option. Construct a set of three to five puzzles, then combine them on
the Set tab.

If you are careful with the number of each shape, you should be able to fit them
all on one large custom punchout. To avoid unused shapes, follow these rules:

* Total number of I's, O's, and T's are each an even number.
* Total number of J's match total number of L's.
* Total number of S's match total number of Z's.
* Maximum number of any shape in any of the puzzles must not be more than half
  of the total number of that shape. For JL and SZ pairs, it's the maximum
  number of a pair in any of the puzzles versus total number of that pair.

The list of puzzles and the status bar will list the "extra" shapes in each
puzzle and in total. It's fine to have "extra" shapes in each puzzle, so long
as they cancel each other out. Try to construct the smaller puzzles before the
larger puzzles in a set, because it's easier to adjust the shape counts in the
larger puzzles.

[New York Times]: https://www.nytimes.com/2018/09/14/crosswords/how-to-make-a-crossword-puzzle-the-series.html
[Qxw builder]: https://www.quinapalus.com/qxw.html
[manual]: https://www.quinapalus.com/qxw-guide-20200708.pdf
[Phil grid builder]: https://www.keiranking.com/apps/phil/
[quick-and-dirty guide]: https://snarky.ca/a-quick-and-dirty-guide-on-how-to-install-packages-for-python/
[PySide6 bug]: https://bugreports.qt.io/browse/PYSIDE-1547
[Show and Tell]: https://github.com/donkirkby/four-letter-blocks/discussions/categories/show-and-tell
[Game Crafter]: https://www.thegamecrafter.com/make/products/CustomLargePunchout
