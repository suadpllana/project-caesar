"""Write the sample programs that ship in /app/progs.

The two scale programs are drawn from the same builders as the graded ones but at an authoring
seed, so timing them locally measures the real shapes without handing over a program the run
will be marked on. The two small ones are written here rather than generated, because they
exist to show the format.

    python authoring/stale-cover-serve/make_progs.py
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

TINY = """h 4 0 8
w 1 10
w 3 30
c
r 0 4 0
r 1 3 0
"""

PAIR = """h 6 1 2
w 0 1
w 3 2
w 6 3
w 9 4
c
r 0 4 0
w 2 8
c
w 7 9
c
r 5 9 0
r 0 9 30
r 0 9 0
"""


def main():
    gen = lab.gen()
    out = lab.SRC / "progs"
    out.mkdir(parents=True, exist_ok=True)
    (out / "tiny.txt").write_text(TINY, encoding="utf-8", newline="\n")
    (out / "pair.txt").write_text(PAIR, encoding="utf-8", newline="\n")

    span, steps, rounds = gen.DEEP[0]
    rng = random.Random("sample/deep")
    lines = gen.deep(rng, span, steps, rounds)
    (out / "deep.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    steps, rounds = gen.WIDE[0]
    rng = random.Random("sample/wide")
    lines = gen.wide(rng, steps, rounds)
    (out / "wide.txt").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    for name in ("tiny.txt", "pair.txt", "deep.txt", "wide.txt"):
        body = (out / name).read_text(encoding="utf-8")
        assert "\r" not in body, "%s picked up CRLF" % name
        print("%-9s %7d lines" % (name, body.count("\n")))


if __name__ == "__main__":
    main()
