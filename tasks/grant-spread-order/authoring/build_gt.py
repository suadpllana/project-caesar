"""Regenerate tests/gt.json, and refuse to write one that has not been proved.

Ground truth here covers the enumerated cases only. The three hundred generated journals
are graded against the sealed model at trial time, after the nonce exists, so there is no
ground truth for them to hold and nothing to paste. gt.json is therefore a tripwire rather
than the answer key: the grader requires the model to reproduce it, so a drift in
oracle.py fails loudly instead of quietly regrading the task.

Two proofs run before anything is written, and a failure of either aborts:

  1. On every enumerated case, the reference implementation and the sealed model agree
     event for event. Two implementations of one specification, one incremental and one
     recomputing the whole tree after every operation.

  2. On a few thousand random journals, the same. A budget or a ceiling taken from one
     author's implementation is a claim; this is what makes it evidence.

Every writer here passes newline="\\n" on purpose. Path.write_text opens in text mode, and
on Windows that turns every newline into a carriage return pair - which is how an earlier
task in this repo shipped a ground truth full of CRLF and was rejected by the structural
check on a file nobody had edited.
"""

import argparse
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "tests"))
sys.path.insert(0, str(HERE))

import cases  # noqa: E402
import gen  # noqa: E402
import harness  # noqa: E402
import oracle  # noqa: E402


def where(a, b):
    for i, (x, y) in enumerate(zip(a, b)):
        if x != y:
            return "row %d\n  ref: %r\n  mod: %r" % (i, x, y)
    if len(a) != len(b):
        return "length %d vs %d" % (len(a), len(b))
    return ""


def prove_cases():
    bad = []
    for name in sorted(cases.PROGS):
        text = cases.PROGS[name]
        gap = where(harness.ref(text), oracle.rows(text))
        if gap:
            bad.append("%s: %s" % (name, gap))
    return bad


def prove_random(n):
    bad = []
    for i in range(n):
        text = gen.text("gt/%d" % i)
        gap = where(harness.ref(text), oracle.rows(text))
        if gap:
            bad.append("gt/%d: %s" % (i, gap))
            if len(bad) > 3:
                break
    return bad


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fuzz", type=int, default=1500)
    args = ap.parse_args()

    bad = prove_cases()
    if bad:
        print("enumerated cases disagree; refusing to write ground truth")
        for line in bad:
            print(" ", line)
        return 1
    print("enumerated: %d cases, reference and model agree" % len(cases.PROGS))

    bad = prove_random(args.fuzz)
    if bad:
        print("random journals disagree; refusing to write ground truth")
        for line in bad:
            print(" ", line)
        return 1
    print("random: %d journals, reference and model agree" % args.fuzz)

    book = {name: oracle.rows(cases.PROGS[name]) for name in sorted(cases.PROGS)}
    out = ROOT / "tests" / "gt.json"
    out.write_text(json.dumps(book, sort_keys=True, separators=(",", ":")) + "\n",
                   newline="\n")
    rows = sum(len(v) for v in book.values())
    print("wrote %s: %d cases, %d rows" % (out, len(book), rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
