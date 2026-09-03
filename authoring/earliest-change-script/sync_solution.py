#!/usr/bin/env python3
"""Write solution/change_script.py from tests/reference.py.

The reference exists once, in tests/reference.py, where the grader reads it.
The solution the platform runs is the same code under a docstring written for
a reader rather than for a grader, and this script is the only thing that
writes it, so the two cannot drift apart. Run it after any edit to the
reference; the diff it leaves should be the docstring and nothing else.
"""

import pathlib

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "earliest-change-script"
REFERENCE = TASK / "tests" / "reference.py"
SOLUTION = TASK / "solution" / "change_script.py"

DOCSTRING = '''"""Reference solution.

The rule has three tiers and the first two are two different quantities.
Fewest moves is what every fast diff computes, and the question it asks at
each position -- does dropping this line still leave a shortest script -- is
answered by knowing how many moves remain from the neighbour you would land
on. Fewest comments is a second quantity with its own recurrence, and it is
not the count of runs of moves: two runs with only a kept line or two between
them are one comment, so what a position has to carry is how many keeps have
gone by since the last move, held at CONTEXT once it reaches it. A run that is
already open is that count at zero. It only has to be known on cells that lie
on some shortest path, since nothing else can be on the answer, and that
restriction is what makes it affordable at all.

The graded pairs sit in two places and neither engine covers the other.

The first is the frontier, run from the far end. Layer d holds, for every
diagonal, the earliest position from which the end is reachable in d moves.
Once every layer is kept, "is this neighbour still on a shortest path?" is one
lookup. Along a diagonal that answer turns from no to yes at one row and stays
yes, so from any position the next cell where a drop or an add becomes
possible is a lookup too, and every cell before it can only be kept through.
The comment counts are computed on those decision cells alone, CONTEXT + 1 to
a cell. The stretch between two decision cells cannot merely be skipped,
because the keeps in it are exactly what carries a position away from the last
move, so it is measured and added on. It costs the square of the number of
moves plus the decision cells, and does not care how long the pair is: a
million lines that differ in three hundred places is a fifth of a second, and
fifty thousand crowded lines that differ in a few thousand is a couple of
seconds. Ask it for a pair that shares no order at all, where the moves run
past the length of the file, and it is finished by nobody.

The second is thresholds over suffixes: hold, for each k, the largest j from
which the tail of the other side still shares k lines. One pass from the far
end maintains that array and it only changes where the two sides match, so it
costs the number of matching positions rather than the length of the pair,
and it hands every match its rank -- how many keeps a shortest script can
still make from it. The matches of one rank form a staircase, so the matches
of the next rank that a given one can still reach are a contiguous stretch of
the next staircase. Under a rule that merely counted runs, one sliding window
over that stretch would do. It will not do here: the keep straight down the
diagonal carries the keep count forward while every other keep in the stretch
resets it, so that one has to be held out of the window rather than merely
compared against it. Holding it out is what splits the stretch in two -- one
more row down, or one more column across -- and each of those is contiguous
in a staircase, so it is two sliding windows and not one. The walk then never
leaves the staircases: each move it considers narrows the stretch it can still
land in, and the question at every step is whether a keep carrying the
required count is still inside. On a third of a million nearly-distinct lines
put back in a different order that is a few seconds, because almost nothing in
such a pair matches anything.

Which engine answers a pair is decided by cost. The frontier is tried first
under a limit, and abandoned once the layers it has built would cost more than
the thresholds would have cost from the start. That figure has to be counted,
and the pass that counts it pays for itself.

Two details are load-bearing. Cutting the shared head and tail off before
starting changes the answer, because a drop is preferred over a keep whenever
both leave the script shortest and as cheap in comments, so the first move is
not always a keep even when the two sequences begin with the same line. And
the count a cell carries depends on how far the walk arrived from the last
move, not merely on whether a run was open, so a pair of numbers per cell is
not enough: it takes one for every distance up to the cap, and that is what
makes the walk's choice at every decision cell a comparison rather than a
search.
"""
'''


def main():
    text = REFERENCE.read_text()
    body = text[text.index("from bisect import bisect_left"):]
    SOLUTION.write_text(DOCSTRING + "\n" + body, newline="\n")
    print("wrote %s (%d lines)" % (SOLUTION, len(SOLUTION.read_text().split("\n"))))


if __name__ == "__main__":
    main()
