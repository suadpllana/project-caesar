"""No graded value may come down to a name the submission chose.

Two checks. The first is lexical: every token the ledger carries has to come from the script
the host was given or from the host's own counting, never from an identifier a submission
picks. The second is the mirror - the reference with every choosable name changed - which
has to produce the same ledger row for row; if it does not, some graded value was reading a
name rather than the machine.

Usage:
    python3 authoring/pack-bind-retire/tiecheck.py [count]
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.abspath(os.path.join(HERE, "..", "..", "tasks", "pack-bind-retire"))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))

import readings as RD  # noqa: E402

TAGS = ("ld", "us", "dp", "rl")


def tokens_of(text):
    names = set()
    for ln in text.splitlines():
        w = ln.split()
        if w and w[0] in ("pk", "pv", "rq", "wk", "nd", "st", "ld", "us", "dp"):
            names.update(w[1:])
    return names


def main(argv):
    count = int(argv[0]) if argv else 200
    corpus = RD.enumerated() + RD.generated(count)
    mirror = os.path.join(HERE, "variants", "ok-mirror")
    bad = 0
    stray = 0
    for nm, text in corpus:
        ref = RD.run(RD.REFERENCE, text)
        mir = RD.run(mirror, text)
        if ref != mir:
            bad += 1
            for a, b in zip(ref, mir):
                if a != b:
                    print("%s: reference %r, mirror %r" % (nm, a, b))
                    break
        # The first column is the script's own file name, which the harness chooses and
        # the host only echoes, so it is not a name the submission gets to pick.
        allowed = tokens_of(text) | {nm, "-", "none", "bad", "off"} | set(TAGS)
        allowed |= {row.split()[0] for row in ref if row.split()}
        for row in ref:
            for tok in row.split():
                if tok in allowed or tok.isdigit():
                    continue
                stray += 1
                print("%s: ledger token %r comes from neither the script nor the counting"
                      % (nm, tok))
    print("%d scripts: %d mirror disagreements, %d stray tokens" % (len(corpus), bad, stray))
    return 1 if (bad or stray) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
