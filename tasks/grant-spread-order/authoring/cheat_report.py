"""Which test catches each cheat, and on how many journals.

A cheat that scores 0 has proved nothing until you know why. The two failures worth
catching here are a cheat that dies on a NameError - rejected by the interpreter rather
than by the verifier - and a cheat aimed at one rule that is caught by a different test
before its own rule is ever reached.

The count column is the lottery check. A cheat that differs from the reference on a
handful of journals out of hundreds is not testing expertise, it is testing luck: under
all-or-nothing grading a rule that rare passes or fails on the draw. Anything in single
digits wants either a sharper enumerated case or a generator that produces the situation
more often.

    python authoring/cheat_report.py
    python authoring/cheat_report.py --count 120
"""

import argparse
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "tests"))

import trial  # noqa: E402


FAILED_LINE = re.compile(r"::(test_\w+)")


def caught(text):
    """The short summary pytest prints under -rf: one FAILED line per failing test."""
    names = []
    for line in text.splitlines():
        if not line.startswith("FAILED"):
            continue
        hit = FAILED_LINE.search(line)
        if hit and hit.group(1) not in names:
            names.append(hit.group(1))
    return names


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--count", type=int, default=80)
    ap.add_argument("--only", default=None)
    args = ap.parse_args()

    scripts = sorted((ROOT / "cheat").glob("*.sh"))
    if args.only:
        scripts = [s for s in scripts if args.only in s.stem]
    bad = 0
    print("%-40s %-6s %s" % ("cheat", "reward", "caught by"))
    for path in scripts:
        name, reward, text = trial.go(path.stem, None, path, args.count)
        names = caught(text)
        if "NameError" in text or "ImportError" in text or "SyntaxError" in text:
            names.append("!! died on an interpreter error, not on a rule")
        if reward != 0:
            names.append("!! SCORED 1")
            bad += 1
        if not names:
            names = ["(no test named - check by hand)"]
            bad += 1
        print("%-40s %-6d %s" % (path.stem, reward, ", ".join(names)))
    print("\n%d cheats, %d wanting attention" % (len(scripts), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
