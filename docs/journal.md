## Developer Journal
### July 2021
Started the project by learning how to draw with the PySide6 library and
building some classes to hold crossword puzzle data.

### August 2021
Add tools for editing the grid and clues. Publish [first puzzle] on Stack
Exchange, and publish first release of the software.

Add suits for larger grids.

[first puzzle]: https://puzzling.stackexchange.com/q/111376/38

### May 2022
Start working on a laser-cut version. The first attempt in wood didn't turn out
well.

![[Prototypes]](images/prototypes.jpg)

[Prototypes]: images/prototypes.jpg

### June 2022
Second laser-cut attempt with Game Crafter. Proof of concept is a set of
tetrominoes for the Donimoes project.

Also start to add warnings when editing a grid and blocks.

### Aug 2022
After a successful proof of concept, start working on packing a set of puzzles
on both sides of a chip board punchout. Also display hints on which block shapes
are needed to balance a set of puzzles.

### Sep 2022
Avoid problems with cutter drift, and purchase the first full prototype of a
puzzle set.

### Oct 2022
Start working on a pair of puzzles in a frame, with jigsaw puzzle tabs to join
the pieces firmly. Finding a complementary set of blocks that don't have
identical solutions is hard! Experiment with evolutionary search.

First full prototype arrives, and it worked. Some nicks didn't hold, and the
plain white backgrounds are boring. Try textured backgrounds and remove
duplicate cut lines.

Experimenting with changes to evolutionary search. The totally random mutation
averages 199 +/- 121 epochs over 33 trials to fill the back grid with no
restrictions. Mutating by removing the blocks closest to one of the gaps
averages 224 +/- 119 epochs over 204 trials. Bizarrely, adding pairing made it
worse! Not only did it increase to 481 +/- 216 epochs over 29 trials, but each
epoch was noticeably slower.

### Nov 2022
Switch from background wood texture to shaded pattern. Distribute background
colours around the colour wheel. Expand to two-part frame for 11x11 pair.

### Dec 2022
Switch from HSV to JCh colour model, now lightness looks consistent across
different hues. Dark suits are still hard to see against the background, though.
First prototype of a puzzle pair arrives. Trim the outside of the 9x9 pair's
frame, since the background doesn't bleed all the way to the edge.

Start talking to a manufacturer about bigger production runs.

### Jan 2023
First double frame prototype arrives, as well as JCh colour model. Dark suits
are better, but still hard to see. Use a different font for each puzzle in a
set. Rewrite the musical set to avoid one blank piece.

### Jan 2024
The prototypes are working OK, but a manufacturer said that the piece tabs are
too small to punch out. Packing without rotation would let me use single tabs
instead of the rotationally symmetrical double tabs, so they could be twice as
big. Start working on packing without rotation, which is much harder.

### Feb 2024
Try calculating all available slots for each shape before packing begins.

### Dec 2024
Try packing both sides at the same time.

### Feb 2025
Add a two-sided evolutionary block packer.

### May 2025
Try building a set that's printed on one side, with blank dry-erase surface on
the back. Then you could copy the letters for any puzzle onto those pieces.

### Sep 2025
First prototype of dry-erase pieces arrives, but copying is way too fiddly. You
have to find the right shapes, copy the letters and the numbers, and then solve.
It takes longer to set up than to solve.

The single tabs are nice, though.

[![dry erase]][dry erase]

Weirdly, the printed side has over 5mm of drift this time, and is unusable. I
don't think any of the other prototypes have had more than 1mm of drift. Very
disappointing!

To try and get the packing without rotation to work, I discovered Knuth's
[algorithm X] for exact cover problems, which the packing seems to be. Luckily,
our [library] provides access to O'Reilly's copy of
[The Art of Computer Programming]. On first read through, it seems promising,
and I found the [xcover] library that seems to have implemented it in Python
with Numba just-in-time compilation.

Soon after, I switched from xcover to [miniexact], since it supports colours
and multiplicity.

[dry erase]: images/dry-erase.jpg
[algorithm X]: https://en.wikipedia.org/wiki/Knuth%27s_Algorithm_X
[library]: https://auth.vpl.ca/ext/scripts/access/index.php?resource=OReilly&assetid=9780134671857
[The Art of Computer Programming]: https://learning.oreilly.com/library/view/the-art-of/9780134671857/ch07b.xhtml
[xcover]: https://pypi.org/project/xcover/
[miniexact]: https://github.com/miniexact/miniexact

### Oct 2025
Switch from using a solver for the front and another for the back to making
each option double sided, and using one solver.

Try switching to pentominoes. One nice outcome was a more logical grouping
of shapes into families that include rotation and flipping. It didn't help
performance, though, so I left it on a dead branch that you can find from
[issue 65].

[issue 65]: https://github.com/donkirkby/four-letter-blocks/issues/65

### Nov 2025
Tried filtering options down to the most common ones in single-sided solutions,
but it didn't help performance.

Went back to Knuth's [original DLX], and found that the option for making
random choices during search often found the first solution faster than the
default search order. Wrote a proof of concept that runs several short searches
with different random seeds, instead of one long search, and it successfully
solved an 11x11 pair within 45 minutes.

Got some [ideas] from Max Heisinger, and found that DLX-PRE dropped the 11x11
solution down to 10 minutes by eliminating redundant items and unusable
options. See the [problems] folder for some example inputs of different sizes.

| Scenario     | Time (Gmems) |
|--------------|--------------|
| original 9x9 |          4.1 |
| filtered 9x9 |          3.4 |

[original DLX]: https://cs.stanford.edu/~knuth/programs.html
[ideas]: https://github.com/miniexact/miniexact/issues/6#issuecomment-3567907089
[problems]: problems/

### Dec 2025
Make it easier to start with manual packing, then finish with miniexact solver.
Successfully packed a set of four puzzles from 9x9 to 13x13, a pair of 9x9
puzzles, a pair of 13x13 puzzles, and a pair of 15x15 puzzles.

### Jun 2026
Work on a fill thread class, for packing in the UI. Switch SVG DPI to 72, since
1000 DPI made it really hard to review on Game Crafter, and may have caused
really bad drift. Add frame pieces to puzzle sets, which might be an easier
alternative to puzzle pairs, particularly 11x11 and 13x13.

### Jul 2026
Merge the new packing code into the UI, and order the first prototype in almost
a year.