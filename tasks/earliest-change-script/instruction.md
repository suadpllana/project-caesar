Two people on my team ran the same pair of files through two different review
tools last month and got two different change scripts back. Both were as short
as a script can be. They disagreed about which lines survived. For a human
reader that is fine, and for us it is not, because we hang review comments off
the moves in the script, and a comment that jumps when the backend changes is a
bug waiting to be filed. So we pinned the answer. One rule, one script, whoever
computes it.

Write `/app/change_script.py`. It defines one function:

```python
def changes(before, after):
    ...
```

`before` and `after` are lists of strings, either of which may be empty. Return
a list of pairs. `("-", i)` drops `before[i]`. `("+", j)` adds `after[j]`. Pairs
may be tuples or two-item lists, and the indices are plain integers.

To read a script back, walk both lists from position zero. A drop consumes one
line of `before`. An add emits one line of `after`. A position no move mentions
is a keep, which consumes one line from each side, and those two lines have to
be equal. Follow the moves in order and what comes out is `after`.

## The rule

There are two parts to it.

The script is as short as it can be. Count the drops and the adds together; no
other script for that pair may use fewer moves.

That still leaves several scripts for most pairs, so the second part chooses
between them. Read a script back the way the paragraph above reads it and write
down what happens at each position of the walk, which is a drop, an add or a
keep. Every shortest script for the same pair gives a reading of the same
length. Order those readings by putting a drop ahead of an add and an add ahead
of a keep, compare two of them position by position from the start, and ours is
the one that comes first. Nothing else enters into it.

## Two examples

`before` is `["m", "z"]` and `after` is `["z", "m"]`. Two moves is the best
anyone can manage. Add the "z" at the front and drop the "m" at the end, or drop
the "m" at the front and add it at the end, both are two moves and both are
shortest. The rule takes the second: `[("-", 0), ("+", 1)]`.

Now `before` is `["a", "a", "b"]` and `after` is `["a", "b", "a"]`. The answer
is `[("-", 0), ("+", 2)]`.

## Speed

Eighteen of the graded pairs are large, and they are drawn across the whole
spread of what we get in production. They run from forty thousand to a million
lines a side. Some differ from their partner in a few hundred places, some
share no order with it worth the name and answer to a script longer than a
third of the file, and the rest are somewhere in between. Some are built from
a handful of distinct lines repeated the whole way down, some are very nearly
all distinct. How long a pair is, how much order it keeps and how often a line
repeats do not move together across the eighteen.

Each of them gets fifteen seconds of wall clock, measured from outside your
process, from the moment it starts to the moment it answers. That fifteen
seconds covers reading the pair in as well. A separate block of four hundred
pairs, a few hundred to fifteen hundred lines each, shares a budget of thirty
seconds for the block. Everything else is short and is not timed.

Their answers are graded as well as their timings, and at that size the
alignment is every bit as ambiguous as it is in the two examples above.

## How you're graded

Fifty-four fixed pairs written out by hand. Twelve thousand random pairs drawn
from between two and six distinct lines, up to forty lines a side. Forty
thousand more from crossing every short shape with every other short shape,
because a random draw hardly ever lands on the pair where two shortest scripts
disagree. Then the four hundred medium pairs and the eighteen large ones. Every
case has to match exactly, in the moves and in their order. There is no partial
credit, and part of the distribution is regenerated from a fresh seed on every
run.

## What the grading process gives you

Your module is imported in a fresh process with nothing importable but the
Python standard library. Anything you install while working on this will not be
there, so the file has to stand on its own. `changes` is called many times in
one process and has to answer the same way every time. Printing is harmless but
pointless, since standard output is redirected before your code runs.

You have 14400 seconds to complete this task. Do not cheat by using online solutions or hints specific to this task.
