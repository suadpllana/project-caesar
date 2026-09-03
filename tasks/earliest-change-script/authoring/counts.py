#!/usr/bin/env python3
"""How far each wrong reading is from the rule, on the blocks that are graded.

Every number quoted in task.toml and in the cheat docstrings comes from here.
A reading that moves only a handful of cases is a lottery ticket rather than a
test of expertise, and one that moves none is a cheat that proves nothing, so
the point of this script is to keep those claims measured rather than argued.
"""

import pathlib
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "cheat"))

import casegen
import oracle

N_RANDOM = 12000

READINGS = [
    "count_runs_not_comments",
    "lex_first_only",
    "slide_the_runs_afterwards",
    "split_the_replacements",
    "delegate_to_difflib",
    "table_walk",
    "two_engines_only",
    "cells_on_shortest_paths",
]


def main():
    shapes = casegen.shapes()
    blocks = [
        ("fixed", list(casegen.FIXED)),
        ("enumerated", [([c for c in u], [c for c in v])
                        for u in shapes for v in shapes]),
        ("random", casegen.random_cases(N_RANDOM, 0)),
    ]
    truth = {label: [[tuple(op) for op in oracle.script(b, a)] for b, a in cases]
             for label, cases in blocks}
    print("%-26s %s" % ("reading", "  ".join("%-16s" % label
                                             for label, _ in blocks)))
    for name in READINGS:
        module = __import__(name)
        row = []
        for label, cases in blocks:
            wrong = 0
            for (b, a), expected in zip(cases, truth[label]):
                if [tuple(op) for op in module.changes(b, a)] != expected:
                    wrong += 1
            row.append("%-16s" % ("%d/%d" % (wrong, len(cases))))
        print("%-26s %s" % (name, "  ".join(row)))


if __name__ == "__main__":
    main()
