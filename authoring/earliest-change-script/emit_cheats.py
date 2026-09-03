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

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "earliest-change-script"
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

FRONTIER_ONLY_DOC = '''"""Deliberate cheating attempt. NEVER executed by the pipeline.

Strategy: stop one engine short. The rule is computed exactly -- keeps since
the last move carried through the walk, comments merged across a kept line or
two, the recurrence evaluated only where a shortest path can reach -- and the
frontier answers twelve of the eighteen timed pairs comfortably, which is
every pair whose two sides still resemble each other. A million lines that
differ in a few hundred places take a fifth of a second, and fifty thousand
crowded lines that differ in a few thousand take a few seconds more. Having
built that, there is nothing in the task's own worked examples to say a second
engine is needed at all.

The six that share no order have nothing left to answer them. Their scripts
run past the length of the file, so the number of moves is in the hundreds of
thousands and the frontier is out by orders of magnitude; what it falls back
on is the table, which is out by more. Every correctness block passes, six of
the eighteen timed pairs never come back, and it scores zero.
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


def emit_frontier_only():
    text = REFERENCE.read_text()
    body = text[text.index("from bisect import bisect_left"):]
    swaps = [
        ('    if engine == "pairs":\n        return _pairs_engine(a, b, n, m)\n\n', ""),
        ('    limit = 1 << 30 if engine == "frontier" else _frontier_limit(\n'
         "        _pairs_cost(a, b, n, m))\n",
         "    limit = _FRONTIER_CAP\n"),
        ("    if layers is None:\n        return _pairs_engine(a, b, n, m)\n",
         "    if layers is None:\n        return _table(before, after)\n"),
    ]
    for old, new in swaps:
        if old not in body:
            raise SystemExit("anchor missing, the reference moved:\n%r" % old[:70])
        body = body.replace(old, new, 1)
    # the pairs engine is now unreachable; cut it out so the file is what it says
    start = body.index("# ------------------------------------------------------------ pairs engine --")
    body = body[:start]
    oracle = ORACLE.read_text()
    table = oracle[oracle.index("INF = (1 << 30"):oracle.index("def comments_in(")].rstrip()
    table = table.replace("def table(before, after):", "def _table_of(before, after):")
    table = table.replace("def script(before, after):", "def _table(before, after):")
    table = table.replace("    rest = table(before, after)", "    rest = _table_of(before, after)")
    path = CHEATS / "frontier_only.py"
    path.write_text(FRONTIER_ONLY_DOC + "\n" + body + table + "\n", newline="\n")
    return path


if __name__ == "__main__":
    for path in (emit_table_walk(), emit_frontier_only()):
        print("wrote %s (%d lines)" % (path, len(path.read_text().split("\n"))))
