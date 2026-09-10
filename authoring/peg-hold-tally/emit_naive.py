"""Write the cheat that settles every rule correctly and still cannot finish in time.

This is the memorised model of a checkpoint - a reference taken over everything the volume holds
the moment it is made - and it is the plan the brief is written against. It agrees with the
definitional settling on every program measured (`handcheck.py naive`, `diff.py naive`), so its
zero is the execution limit and nothing else, which is the one thing the rest of the cheat suite
cannot show.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
SRC = HERE / "naive"
CHEATS = HERE.parent.parent / "tasks" / "peg-hold-tally" / "cheat"
PARTS = ("live.py", "cover.py", "edge.py", "gone.py", "sole.py")


def main():
    out = ["#!/bin/bash",
           "# settles every rule correctly by taking a reference over the live map at each peg,",
           "# which cannot get the graded set through inside the stated limit",
           "set -euo pipefail", ""]
    for part in PARTS:
        body = (SRC / part).read_text(encoding="utf-8").rstrip("\n")
        out.append("cat > /app/keep/%s <<'PYEOF'\n%s\nPYEOF\n" % (part, body))
    text = "\n".join(out) + "\n"
    assert "\r" not in text
    path = CHEATS / "cheat-count-at-peg.sh"
    path.write_text(text, encoding="utf-8", newline="\n")
    path.chmod(0o755)
    print("wrote", path.name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
