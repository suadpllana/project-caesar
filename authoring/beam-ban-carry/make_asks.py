"""Write the programs that ship under /app/asks.

Four: one small enough to read, one with two requests, and the two shapes the execution limit
is about, so the limit can be measured from inside the tree rather than guessed at.
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gen  # noqa: E402

OUT = HERE.parent.parent / "tasks" / "beam-ban-carry" / "environment" / "app_src" / "asks"

TINY = """cfg 2 3 2 2 2 6
sc 1 2 9
sc 1 3 6
sc 2 3 8
sc 2 4 7
sc 3 4 9
sc 3 2 5
sc 4 2 8
sc 4 3 4
sc 3 0 5
sc 4 0 3
ask small 1
"""

PAIR = """cfg 3 2 1 1 3 7
sc 1 2 8
sc 1 3 7
sc 1 4 5
sc 2 3 9
sc 2 4 6
sc 2 1 4
sc 3 4 8
sc 3 1 7
sc 3 2 3
sc 4 1 9
sc 4 2 5
sc 4 3 2
sc 2 0 6
sc 4 0 4
ask left 1 2
ask right 3
"""


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "tiny.txt").write_text(TINY, encoding="utf-8", newline="\n")
    (OUT / "pair.txt").write_text(PAIR, encoding="utf-8", newline="\n")
    for name, fam in (("long.txt", "wide"), ("turn.txt", "churn")):
        lines = gen.make(fam, random.Random("ship|%s" % fam))
        (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    for one in sorted(OUT.iterdir()):
        body = one.read_text(encoding="utf-8")
        if "\r" in body:
            raise SystemExit("carriage return in %s" % one)
        print("%-10s %4d lines" % (one.name, len(body.splitlines())))


if __name__ == "__main__":
    main()
