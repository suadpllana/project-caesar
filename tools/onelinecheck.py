#!/usr/bin/env python3
"""How short is the answer? The easiness probe, asked mechanically.

`delta-view-retraction` failed the easiness probe twice, and both times the winning
submission was written before the solver ran a single experiment, because the graded
decision was reproducible by one comparison between two fields the environment already
exposes:

    2026-08-14, 2 of 3:  sum(acc.top.values()) == acc.n     "nothing was dropped"
    2026-08-14, 3 of 3:  acc.n == len(cell.dep)             the same test, other pair

Deleting the field named `spill` did nothing, because the information was still there in
the difference between two fields that were each individually innocent. A leak audit that
looks for named giveaways cannot see that. This can.

WHAT IT DOES. A task supplies `authoring/decisions.py` with a `samples()` function
returning the graded decisions its reference makes, each as a row of integer features read
off state the agent can see at that moment, plus the label the reference chose. This
searches for the shortest exact rule over those features:

    depth 1   a == b, a < b, a <= b, a != b, a == <small constant>, label == a
    depth 2   any two depth-1 terms joined by and / or

A rule that reproduces the label on every sample is an answer a frontier model writes
cold, whatever the surrounding prose says. Two terms is still cold: the 3-of-3 solve above
was three terms and took one write.

THE VERDICT, and it is about the task rather than about any one question. A task is at
risk when EVERY graded quantity has an exact rule at depth <= 2. It is defensible when at
least one of them does not, because that is the thing a solver has to discover rather than
guess - and on the task this was built for, that quantity is not the repair decision at
all, it is how much of a group a rebuild has to fold.

This measures the shape of the answer. It cannot tell you the task is hard, only that the
answer is not short. Read it as "not yet known to be trivial".

Usage:
    python3 tools/onelinecheck.py <slug>
"""

from __future__ import annotations

import importlib.util
import itertools
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

CMP = (
    ("==", lambda a, b: a == b),
    ("!=", lambda a, b: a != b),
    ("<", lambda a, b: a < b),
    ("<=", lambda a, b: a <= b),
    (">", lambda a, b: a > b),
    (">=", lambda a, b: a >= b),
)
CONSTS = (0, 1, 2, 3)


def terms(names):
    """Every depth-1 term: field against field, and field against a small constant."""
    for a, b in itertools.permutations(names, 2):
        for sym, fn in CMP:
            yield ("%s %s %s" % (a, sym, b), lambda r, a=a, b=b, fn=fn: fn(r[a], r[b]))
    for a in names:
        for k in CONSTS:
            for sym, fn in CMP:
                yield ("%s %s %d" % (a, sym, k), lambda r, a=a, k=k, fn=fn: fn(r[a], k))


def search(rows, labels):
    """The shortest exact rule, or None. Integer labels are matched by identity first."""
    names = sorted(rows[0])
    if not all(isinstance(v, bool) for v in labels):
        for a in names:
            if all(r[a] == y for r, y in zip(rows, labels)):
                return "= %s" % a
        return None

    single = []
    for text, fn in terms(names):
        hit = [fn(r) for r in rows]
        if hit == labels:
            return text
        single.append((text, hit))

    for (ta, ha), (tb, hb) in itertools.combinations(single, 2):
        if [x or y for x, y in zip(ha, hb)] == labels:
            return "%s or %s" % (ta, tb)
        if [x and y for x, y in zip(ha, hb)] == labels:
            return "%s and %s" % (ta, tb)
    return None


def load(slug):
    """The task's decision rows, from the bundle or from repo-level working material.

    A decisions.py inside tasks/<slug>/ ships with the archive, and the quality
    review rejected one on 2026-09-05 for exactly that: its only reader is this
    tool, which does not ship, so from inside the bundle it is an orphan. The
    repo-level authoring/<slug>/ copy is the one to write.
    """
    outside = ROOT / "authoring" / slug / "decisions.py"
    inside = ROOT / "tasks" / slug / "authoring" / "decisions.py"
    path = outside if outside.is_file() else inside
    if not path.is_file():
        return None, outside
    spec = importlib.util.spec_from_file_location("decisions_%s" % slug.replace("-", "_"),
                                                  path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod, path


def main(argv):
    if len(argv) < 2:
        print(__doc__)
        return 2
    slug = argv[1]
    mod, path = load(slug)
    print("== %s" % slug)
    if mod is None:
        print("   no authoring/decisions.py, so the shape of this task's answer is")
        print("   unmeasured. Write one: it returns the reference's graded decisions as")
        print("   rows of integer features the agent can read, plus the label chosen.")
        print("   Expected at %s" % path)
        return 1

    questions = mod.samples()
    short = 0
    for name, rows in sorted(questions.items()):
        feats = [r for r, _ in rows]
        labels = [y for _, y in rows]
        if not feats:
            print("   %-28s no samples" % name)
            continue
        if len(set(map(str, labels))) == 1:
            print("   %-28s %d samples, one outcome only - not a decision" % (name, len(feats)))
            continue
        rule = search(feats, labels)
        if rule is None:
            print("   %-28s %4d samples  no exact rule at depth <= 2" % (name, len(feats)))
        else:
            short += 1
            print("   %-28s %4d samples  EXACT: %s" % (name, len(feats), rule))

    live = [n for n, rows in questions.items()
            if rows and len(set(str(y) for _, y in rows)) > 1]
    print()
    if short and short == len(live):
        print("   FAIL every graded decision is reproduced by a rule of two terms or")
        print("        fewer over fields the environment already exposes. That is an")
        print("        answer written cold, before any experiment. Either close the")
        print("        pair, or add a graded quantity that a short rule cannot express.")
        return 1
    if short:
        print("   OK   %d of %d graded decisions are short, and %d is not. The task rests"
              % (short, len(live), len(live) - short))
        print("        on the one that is not; check that the instruction does not give")
        print("        it away and that a cheat covers the short ones.")
        return 0
    print("   OK   no graded decision is reproduced by a short rule")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
