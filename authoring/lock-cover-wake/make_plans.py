#!/usr/bin/env python3
"""Write the four sample scripts into environment/app_src/plans/. Never ships.

Every generator that writes a shipped file pins newline="\\n" and checks that no carriage
return survived: zipcheck rejects CRLF in the archive and Git normalising on commit hides it,
because the working copy is what gets zipped.

    python3 -u authoring/lock-cover-wake/make_plans.py
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import gen  # noqa: E402

TINY = """
cfg 3
beg 15
beg 41
beg 24
req 24 0.0 X
req 15 0.0 X
req 24 0 SIX
req 24 0 IS
req 24 0.2 X
req 41 0 X
com 24
req 15 0.3 X
req 15 0.3 X
"""

PAIR = """
cfg 4
beg 6
beg 1
beg 9
beg 3
req 6 2 IX
req 6 2.0 X
req 1 2 IS
req 1 2.1 S
req 9 2 S
req 3 2.0 S
req 1 2.2 S
req 1 2.3 S
req 1 2.4 S
com 6
req 3 5.0 X
req 9 5.0 S
"""


def write(name, lines):
    out = lab.SRC / "plans" / name
    out.parent.mkdir(parents=True, exist_ok=True)
    text = "\n".join(lines) + "\n"
    assert "\r" not in text, name
    out.write_text(text, encoding="utf-8", newline="\n")
    print("%-10s %7d lines  %8.1f kB" % (name, len(lines), len(text) / 1024.0))


def check_cases():
    """tiny.txt and pair.txt are graded as they ship, so the case list must hold the same
    lines: two tools disagreeing is how a rule stops being tested (CLAUDE.md)."""
    sys.path.insert(0, str(lab.TASK / "tests"))
    import cases
    for name in ("tiny", "pair"):
        here = (lab.SRC / "plans" / ("%s.txt" % name)).read_text().strip().splitlines()
        there = cases.prog("plan-%s" % name)
        assert here == there, "plans/%s.txt and case plan-%s have drifted apart" % (name, name)
    print("the two sample scripts match their graded cases")


def main():
    write("tiny.txt", [ln.strip() for ln in TINY.strip().splitlines()])
    write("pair.txt", [ln.strip() for ln in PAIR.strip().splitlines()])
    write("wide.txt", gen.wide(random.Random("sample-wide")))
    write("deep.txt", gen.deep(random.Random("sample-deep")))
    check_cases()
    return 0


if __name__ == "__main__":
    sys.exit(main())
