#!/usr/bin/env python3
"""Write solution/change_script.py from tests/reference.py.

The reference exists once, in tests/reference.py, where the grader reads it.
The solution the platform runs is the same code under a docstring written for
a reader rather than for a grader, and this script is the only thing that
writes it, so the two cannot drift apart. Run it after any edit to the
reference; the diff it leaves should be the docstring and nothing else.
"""

import pathlib
import re

TASK = pathlib.Path(__file__).resolve().parent.parent
REFERENCE = TASK / "tests" / "reference.py"
SOLUTION = TASK / "solution" / "change_script.py"

DOCSTRING = '''"""Reference solution.

The rule has three tiers and the first two are two different quantities.
Fewest moves is what every fast diff computes, and the question it asks at
each position -- does dropping this line still leave a shortest script -- is
answered by knowing how many moves remain from the neighbour you would land
on. Fewest hunks is a second quantity with its own recurrence: a run of moves
that is already open extends for nothing, a keep closes it, and a move after a
keep opens a new one. It only has to be known on cells that lie on some
shortest path, since nothing else can be on the answer, and that restriction
is what makes it affordable at all.

The graded pairs sit in three places and no engine covers two of them.

The first is the frontier, run from the far end. Layer d holds, for every
diagonal, the earliest position from which the end is reachable in d moves.
Once every layer is kept, "is this neighbour still on a shortest path?" is one
lookup. Along a diagonal that answer turns from no to yes at one row and stays
yes, so from any position the next cell where a drop or an add becomes
possible is a lookup too, and every cell before it can only be kept through.
The hunk counts are computed on those decision cells alone, two to a cell --
one for arriving inside a run of moves, one for arriving after a keep -- and
the walk from the start reads them off. It costs the square of the number of
moves plus the decision cells, and does not care how long the pair is: a
million lines that differ in three hundred places is a fifth of a second. Ask
it for a pair that shares no order at all, where the moves run to a third of
the file, and it is finished by nobody.

The second is rows of the prefix table, one big integer each, advanced by the
five-operation bit-parallel step. That gives how many moves remain from every
position and nothing else, so it is where the previous version of this task
stopped; the hunk count still has to be found, and it is only affordable on the
cells that lie on some shortest path. Those are read off row by row from the
bottom up with a handful of integer operations per row. A cell is on a shortest
path when a drop, an add or a keep from it lands on one: the add is a bit of
the row, the keep is a bit of the line's occurrence mask, and the drop asks
whether the table is equal in two consecutive rows at that column, which fails
exactly on the stretches between a column where a step appears in the lower
row and the column where one disappears. Those alternate, so one subtraction
fills every stretch at once. The cells that come out are a few per row on any
pair we have seen, and the hunk recurrence runs on those alone. Sixty thousand
crowded lines that share no order are a few seconds; a million lines are four
minutes, which is why the frontier exists.

The third is thresholds over suffixes: hold, for each k, the largest j from
which the tail of the other side still shares k lines. One pass from the far
end maintains that array and it only changes where the two sides match, so it
costs the number of matching positions rather than the length of the pair,
and it hands every match its rank -- how many keeps a shortest script can
still make from it. The matches of one rank form a staircase, so the matches
of the next rank that a given one can still reach are a contiguous stretch of
the next staircase, and the hunk count of every match comes out of one
sliding window over it. The walk then never leaves the staircases: each move
it considers narrows the stretch it can still land in, and the question at
every step is whether a keep carrying the required count is still inside.
On a third of a million nearly-distinct lines put back in a different order
that is a few seconds, because almost nothing in such a pair matches anything.

So run the frontier and abandon it, layers and all, once the pair turns out to
need more moves than whichever of the other two would have cost from the
start. Two of the three costs are read off the two lengths; the third has to
be counted, and the pass that counts it pays for itself.

Two details are load-bearing. Cutting the shared head and tail off before
starting changes the answer, because a drop is preferred over a keep whenever
both leave the script shortest and as cheap in hunks, so the first move is not
always a keep even when the two sequences begin with the same line. And the
hunk count a cell carries depends on how the walk arrived, inside a run or
after a keep, so a single number per cell is not enough: the pair of them is
what makes the walk's choice at every decision cell a comparison rather than
a search.
"""'''


def main():
    text = REFERENCE.read_text()
    body = re.sub(r'^""".*?"""\n', "", text, count=1, flags=re.DOTALL)
    SOLUTION.write_text(DOCSTRING + "\n" + body, newline="\n")
    print("wrote", SOLUTION.relative_to(TASK), len(body.splitlines()),
          "lines of code under the solution docstring")


if __name__ == "__main__":
    main()
