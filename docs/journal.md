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

[first puzzle]: https://puzzling.stackexchange.com/q/111376/38