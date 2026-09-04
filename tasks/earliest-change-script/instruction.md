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

There are three parts to it, and each one is only consulted where the parts
before it leave a tie.

The script is as short as it can be. Count the drops and the adds together; no
other script for that pair may use fewer moves.

That still leaves several scripts for most pairs. Read a script back the way
the paragraph above reads it and write down what happens at each position of
the walk, which is a drop, an add or a keep. Every shortest script for the same
pair gives a reading of the same length. A run is a stretch of consecutive
moves in that reading, whether drops or adds, with a keep or an end of the
reading on either side of it. One comment hangs off each change, and a run is
not always a change on its own: where fewer than three kept lines separate one
run from the next, the two belong to the same comment, because a reader with a
line or two of untouched code in front of them is still reading one change.
Three kept lines or more and the second run starts a comment of its own. The
first run in a reading always starts one, having nothing in front of it to
join. Of the shortest scripts, ours needs the fewest comments.

Where two shortest scripts need the same number of comments, order their
readings by putting a drop ahead of an add and an add ahead of a keep, compare
the two position by position from the start, and ours is the one that comes
first. Nothing else enters into it.

## Four examples

`before` is `["m", "z"]` and `after` is `["z", "m"]`. Two moves is the best
anyone can manage. Add the "z" at the front and drop the "m" at the end, or drop
the "m" at the front and add it at the end, both are two moves, both are one
comment, and both are shortest. The rule takes the second: `[("-", 0), ("+", 1)]`.

`before` is `["a", "a"]` and `after` is `["a", "b"]`. One drop and one add is
the least that will do it. Dropping the first "a" and adding the "b" at the end
reads drop, keep, add: two runs with a single kept line between them, which is
one comment. Dropping the second "a" reads keep, drop, add, where the two moves
are one run and so also one comment. Neither is cheaper, so the reading order
settles it and the answer is `[("-", 0), ("+", 1)]`.

`before` is `["a", "a", "a"]` and `after` is `["a", "a", "a", "a", "b"]`. Two
adds, and where they go is the whole question. Putting them at positions one
and four reads keep, add, keep, keep, add, which leaves two kept lines between
the runs and takes one comment. Putting the first add at the front instead
leaves three, and costs two. The answer is `[("+", 1), ("+", 4)]`.

Now `before` is `["a", "a", "b"]` and `after` is `["a", "b", "a"]`. The answer
is `[("-", 0), ("+", 2)]`.

## Speed

Eighteen of the graded pairs are large, and they are drawn across the whole
spread of what we get in production. They run from forty thousand to a million
lines a side. Some differ from their partner in a few hundred places and some
in a few thousand; the rest share no order with their partner worth the name
and answer to a script longer than the file. How often a line repeats varies
across that set from a handful of distinct lines standing in for the whole
file to pairs where hardly any line repeats at all.

Each of them gets sixty seconds of wall clock, measured from outside your
process, from the moment it starts to the moment it answers. That sixty
seconds covers reading the pair in as well. A separate block of four hundred
pairs, a few hundred to fifteen hundred lines each, shares a budget of forty
seconds for the block. Everything else is short and is not timed.

Their answers are graded as well as their timings, and at that size the
alignment is every bit as ambiguous as it is in the four examples above.

## How you're graded

Seventy-one fixed pairs written out by hand. Twelve thousand random pairs drawn
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
