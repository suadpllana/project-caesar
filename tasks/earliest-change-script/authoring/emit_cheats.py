#!/usr/bin/env python3
"""Write the cheats that are correct implementations and merely too slow.

Those three have to compute the rule exactly, or they fail the short blocks
and prove nothing about the budgets they were built to fail. The only way to
be sure of that is to cut them out of the model and the reference rather than
to write them again, so this script does that: it takes the definitional
table out of oracle.py, and the engines out of reference.py with one of them
struck out of the dispatch. Run it after any edit to either.

The other cheats are wrong on purpose and are hand-written; they are not
touched here.
"""

import pathlib

TASK = pathlib.Path(__file__).resolve().parent.parent
ORACLE = TASK / "tests" / "oracle.py"
REFERENCE = TASK / "tests" / "reference.py"
CHEATS = TASK / "cheat"

TABLE_DOC = '''"""Deliberate cheating attempt. NEVER executed by the pipeline.

Strategy: write the rule down and walk it. The table holds, for every position
and every number of keeps since the last move, the best pair of numbers a
completion can reach; the walk from the start takes a drop whenever a drop
still reaches the best pair, otherwise an add, otherwise a keep. It is the
rule and nothing else, so it is right on every case small enough for it to
finish, which is every case a person would write out by hand to check
themselves.

It is quadratic in the two lengths, twice over, and it is the answer to
"what if I just do the obvious thing". The medium block alone is four hundred
pairs of a few thousand lines against forty seconds; one of them is already
past that. The timed pairs are between forty thousand and a million lines a
side, where the table is billions of entries and would not fit in memory even
if there were time for it. Every short block passes and everything with a
clock on it fails.
"""
'''

TWO_ENGINES_DOC = '''"""Deliberate cheating attempt. NEVER executed by the pipeline.

Strategy: stop one engine short. The rule is computed exactly -- keeps since
the last move carried through the walk, comments merged across a kept line or
two, the recurrence evaluated only where a shortest path can reach -- and two
of the three families are answered comfortably. A long pair that differs in a
few hundred places belongs to the frontier. A pair of a third of a million
nearly-distinct lines put back in a different order belongs to the thresholds
over suffixes, because almost nothing in it matches anything.

The third family has nothing left to answer it. Forty to sixty thousand lines
drawn from a handful of distinct ones share no order at all, so the frontier
is out by orders of magnitude; and every line in them matches a large fraction
of the other side, so the number of matching positions is the square of the
length over the alphabet and the thresholds are out by more. Rows of the
prefix table are the only affordable thing there, and this does not have them.
Every correctness block passes, six of the eighteen timed pairs never come
back, and it scores zero.
"""
'''


def emit_table_walk():
    text = ORACLE.read_text()
    start = text.index("CONTEXT = ")
    stop = text.index("def comments_in(")
    body = text[start:stop].rstrip() + "\n"
    body = body.replace("def script(before, after):", "def changes(before, after):")
    path = CHEATS / "table_walk.py"
    path.write_text(TABLE_DOC + "\n" + body, newline="\n")
    return path


def emit_two_engines():
    text = REFERENCE.read_text()
    body = text[text.index("from bisect import bisect_left"):]
    swaps = [
        ('    if engine == "rows":\n        return _rows_engine(a, b, n, m)\n', ""),
        ("    rows = _rows_cost(n, m)\n    pairs = _pairs_cost(a, b, n, m)\n"
         "    second = _pairs_engine if pairs < rows else _rows_engine\n",
         "    pairs = _pairs_cost(a, b, n, m)\n    second = _pairs_engine\n"),
        ('    limit = 1 << 30 if engine == "frontier" else _frontier_limit(min(rows, pairs))\n',
         '    limit = 1 << 30 if engine == "frontier" else _frontier_limit(pairs)\n'),
    ]
    for old, new in swaps:
        if old not in body:
            raise SystemExit("anchor missing, the reference moved:\n%r" % old[:70])
        body = body.replace(old, new, 1)
    # the row engine is now unreachable; cut it out so the file is what it says
    start = body.index("# --------------------------------------------------------------- row engine --")
    stop = body.index("# ------------------------------------------------------------ pairs engine --")
    body = body[:start] + body[stop:]
    path = CHEATS / "two_engines_only.py"
    path.write_text(TWO_ENGINES_DOC + "\n" + body, newline="\n")
    return path


if __name__ == "__main__":
    for path in (emit_table_walk(), emit_two_engines()):
        print("wrote %s (%d lines)" % (path, len(path.read_text().split("\n"))))
