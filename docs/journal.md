## Developer Journal
### July 2021
Started the project by learning how to draw with the PySide6 library and
building some classes to hold crossword puzzle data.

### August 2021
Add tools for editing the grid and clues. Publish [first puzzle] on Stack
Exchange, and publish first release of the software.

Add suits for larger grids.

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

[first puzzle]: https://puzzling.stackexchange.com/q/111376/38