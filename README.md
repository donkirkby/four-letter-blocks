# Four-Letter Blocks


[![Package Version]][pypi]
[![Build Status]][actions]
[![Code Coverage]][codecov]

[Package Version]: https://badge.fury.io/py/four-letter-blocks.svg
[pypi]: https://pypi.org/project/four-letter-blocks/
[Build Status]: https://github.com/donkirkby/four-letter-blocks/actions/workflows/build.yml/badge.svg?branch=main
[actions]: https://github.com/donkirkby/four-letter-blocks/actions
[Code Coverage]: https://codecov.io/github/donkirkby/four-letter-blocks/coverage.svg?branch=main
[codecov]: https://codecov.io/github/donkirkby/four-letter-blocks?branch=main

[starter]: docs/images/starter.png
[PDF]: docs/images/starter.pdf
[Construct Your Own]: docs/construct_your_own.md

This is a program for building a new type of puzzle I designed: a crossword
puzzle cut up into blocks of four letters. The solver gets the blocks plus a
set of standard crossword clues and has to assemble the grid. The bad news is
that the clues aren't numbered in the normal way - 1 Across might not be in the
top left. The good news is that every word has at least the first letter given.

Here's a small starter puzzle to see how they work. You can also print out the
[PDF]. Find more challenging puzzles I've published on [Puzzling Stack Exchange].

## Famous Puzzles
Clue numbers are shuffled: 1 Across might not be in the top left.

Across  
**1.** Lamb's mother  
**2.** Polka you can't dance to  
**3.** Small gear  
**5.** __ and Knaves  
**7.** English marshland  
**8.** Go out, like the tide  
**9.** "We __ Family"  
**10.** Seven-piece puzzle  
**13.** Desperately request  
**15.** League of higher learning

Down  
**4.** Sweaty spot  
**5.** Finger lickin' good  
**6.** The One from The Matrix  
**8.** Consume  
**11.** Upper underwear  
**12.** Unstraightening  
**13.** Brought to life  
**14.** WALL·E's love interest  
**16.** A couple  
**17.** Tennis games

[![starter]][starter]

## Solving
To solve a puzzle: print out the PDF, cut out the blocks, and then use the clues
to put the blocks together. Here are a few ideas for how to make the blocks:
1. Printed on paper - easy to make, but frustrating to work with. Moving a piece
   or even breathing will probably move some other pieces around.
2. Printed on cardstock - a bit heavier and a bit less likely to move.
3. Printed on paper, glued to a cereal box - with a bit of thickness and more
   weight, the blocks move better and won't slide over each other.
4. Printed on cardstock, glued to felt - deluxe style. Slides very nicely and
   the blocks bump gently against each other.

Whatever technique you use, glue sticks are easier to work with than white glue.
If you don't want to print it out, you can also download the image and move the
pieces around in a paint program.

## Constructing Your Own
To construct your own puzzle, you have to construct the crossword puzzle, split
it up into blocks of four letters, and then publish it. Read all the details on
the [Construct Your Own] page.

[Puzzling Stack Exchange]: https://puzzling.stackexchange.com/search?q=%5Bcrosswords%5D+%5Bjigsaw-puzzle%5D+user%3A38
