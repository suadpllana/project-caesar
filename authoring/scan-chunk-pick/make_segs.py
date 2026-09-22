"""Write the four segment files that ship in /app/segs.

tiny and pair are written here by hand; wide and deep come from the same two scale shapes the
graded set draws from, at a seed that is not the grading nonce. Nothing but input ships: no
expected output, no annotation, no counts.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "scan-chunk-pick"
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402

OUT = TASK / "environment" / "app_src" / "segs"

TINY = """seg 10 6 2
ch 0 6 0 3 9 e d 3 3 6 9 0 1 2 0 1 2
ch 1 6 0 1 6 e p 1 2 3 4 5 6
qry
prd ge 0 5
prj 1 0
end
"""

PAIR = """seg 25 20 3
ch 0 8 1 50 75 e d 3 50 63 75 0 1 - 2 0 *58 1 2
ch 0 6 0 25 75 w p 31 77 44 68 52 39
ch 0 6 2 10 22 e p 10 - 22 17 - 13
ch 1 5 0 0 4 e p 0 2 4 1 3
ch 1 5 5 - - e p - - - - -
ch 1 10 0 0 9 e d 4 0 3 6 9 0 1 2 3 0 1 2 3 0 1
ch 2 20 3 100 140 w p 104 118 - 137 122 109 - 131 115 126 140 102 - 119 133 107 124 112 138 128
up 0 3 70
up 0 15 44
up 2 12 -
up 1 7 8
del 5
del 17
qry
prd ge 0 40
prd le 2 130
prd nn 1
prj 2 0
end
qry
prd nu 1
prd ne 0 63
prj 0 1
end
"""


def write(name, text):
    assert "\r" not in text
    path = OUT / name
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("wrote %s (%d bytes)" % (path, len(text)))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    write("tiny.txt", TINY)
    write("pair.txt", PAIR)
    for fam in ("wide", "deep"):
        rng = gen._rng("shipped-sample", fam, 0)
        write(fam + ".txt", "\n".join(gen._large(fam, rng)) + "\n")


if __name__ == "__main__":
    main()
