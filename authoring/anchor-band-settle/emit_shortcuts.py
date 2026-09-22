#!/usr/bin/env python3
"""Write the dumb positional and constant shortcut cheats, and measure what each matches.

The contract (docs/INSTRUCTION-CONTRACT.md, Shortcuts) asks for the dumbest constant and
positional strategies and the nop, each scored as a cheat and each with the fraction of cases
it matches recorded - all-or-nothing grading turns a strategy that matches most cases into a 0
and hides thin data, so the fraction is the evidence, not the score.

Each shortcut is a whole submission: a self-contained hold.py and three empty modules, since
the shipped frame driver imports hold and hold here uses neither lay, stick nor pick. The match
counts printed are what the Shortcuts table in trace.md must quote.

    python3 emit_shortcuts.py
"""
import stat
import sys

import lab

CHEATS = lab.TASK / "cheat"

# The worked example's correct output (instruction.md: small.txt should read `1 31 b4`).
SMALL = ["1 31 b4", "2 358 off scroll", "3 342 b12", "4 253 off scroll"]

CONST = '''# constant: the most common offset and the most common word in the ground truth
def start(v):
    pass


def before(v):
    pass


def after(v):
    return 0, "off scroll"
'''

POSFIRST = '''# positional: hold by the first laid-out box of the document, at the old offset
def start(v):
    pass


def before(v):
    pass


def _first(v):
    stack = list(reversed(v.kids))
    while stack:
        b = stack.pop()
        if not b.lift and not b.gone:
            return b
        stack.extend(reversed(b.kids))
    return None


def after(v):
    b = _first(v)
    return max(v.s, 0), ("none" if b is None else b.id)
'''

REPLAY = '''# the worked example's output replayed by frame number
LINES = %r
STATE = {"n": 0}


def start(v):
    STATE["n"] = 0


def before(v):
    pass


def after(v):
    n = STATE["n"]
    STATE["n"] = n + 1
    if n < len(LINES):
        part = LINES[n].split(" ", 2)
        return int(part[1]), part[2]
    return max(v.s, 0), "none"
''' % (SMALL,)

SHORTCUTS = {
    "const-lines": ("prints a constant `0 off scroll` for every frame", CONST),
    "pos-first-box": ("holds by the first laid-out box of the document, at the old offset", POSFIRST),
    "replay-small": ("replays the worked example's four lines by frame number", REPLAY),
}


def files(hold):
    return {"lay.py": "\n", "stick.py": "\n", "pick.py": "\n", "hold.py": hold}


def script(why, hold):
    body = ["#!/bin/bash", "# " + why, "set -euo pipefail", ""]
    for part, text in files(hold).items():
        body += ["cat > /app/view/%s <<'PYEOF'" % part, text.rstrip("\n"), "PYEOF", ""]
    return "\n".join(body) + "\n"


def main():
    CHEATS.mkdir(exist_ok=True)
    cases, _gen, model = lab.sealed()
    truth = {c: model.expect(cases.prog(c)) for c in cases.ORDER}

    def matches(built):
        tree = lab.tree(files=built)
        return sum(1 for c in cases.ORDER
                   if lab.run_text(tree, "\n".join(cases.prog(c)) + "\n") == truth[c])

    nop = lab.tree(None)
    nhits = sum(1 for c in cases.ORDER
                if lab.run_text(nop, "\n".join(cases.prog(c)) + "\n") == truth[c])
    print("nop            matches %d of %d enumerated" % (nhits, len(cases.ORDER)))

    for name, (why, hold) in SHORTCUTS.items():
        hits = matches(files(hold))
        if hits == len(cases.ORDER):
            raise SystemExit("%s matches every enumerated case - regenerate the data" % name)
        out = CHEATS / ("cheat-%s.sh" % name)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(script(why, hold))
        out.chmod(out.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print("%-14s matches %d of %d enumerated -> %s"
              % (name, hits, len(cases.ORDER), out.name))
    return 0


if __name__ == "__main__":
    sys.exit(main())
