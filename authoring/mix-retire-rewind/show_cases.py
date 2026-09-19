"""Dump the enumerated plans' traces from all three implementations, with a shape check.

A case that pins a retirement has to actually reach one, and a case that pins the record has to
print one; a plan that never reaches its own decision looks fine and tests nothing.
"""
from __future__ import annotations

import pathlib
import sys

import lab

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "seal"))

import cases  # noqa: E402
import model  # noqa: E402


def main(argv):
    want = [a for a in argv if not a.startswith("-")]
    loud = "-q" not in argv
    work = [(n, "\n".join(cases.ops(n))) for n in cases.ORDER if not want or n in want]
    ref = lab.run_many(lab.reference(), work)
    slow = lab.run_many(HERE / "slow" / "walk", work)
    bad = 0
    for name, _text in work:
        lines = cases.ops(name)
        good = model.expect(lines)
        got = ref[name]["got"]
        walked = slow[name]["got"]
        note = []
        if got is None:
            note.append("REFERENCE RAISED %s" % ref[name]["err"])
        elif got != good:
            note.append("REFERENCE DIFFERS")
        if walked is None:
            note.append("WALKER RAISED %s" % slow[name]["err"])
        elif walked != good:
            note.append("WALKER DIFFERS")
        if name.startswith(("hold-", "mix-", "edge-")) and not any(":gone" in ln for ln in good) \
                and name not in ("hold-zero-runs-on",):
            note.append("no retirement reached")
        if not good:
            note.append("prints nothing")
        if note:
            bad += 1
        print("== %-26s %d lines %s" % (name, len(good), " ".join(note)), flush=True)
        if loud:
            for line in good:
                print("     " + line[:200], flush=True)
    print("%d cases, %d with findings" % (len(work), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
