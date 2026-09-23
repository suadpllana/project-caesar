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

def page(g, vals, flag, form="v", dic=None):
    """One page line, its header worked out from its values."""
    live = [v for v in vals if v is not None]
    nulls = len(vals) - len(live)
    if live:
        mn, mx = min(live), max(live)
        if flag == "w":
            mn, mx = -(-mn // g) * g, (mx // g) * g
            assert mn <= mx, vals
        lo, hi = str(mn), str(mx)
    else:
        lo = hi = "-"
    at = {v: i for i, v in enumerate(dic or ())}
    toks = ["-" if v is None else str(at[v] if form == "i" else v) for v in vals]
    return " ".join(["pg", str(len(vals)), str(nulls), lo, hi, flag, str(sum(live)), form] + toks)


def _tiny():
    g = 10
    return "\n".join([
        "seg 10 6 2",
        "ch 0 d 3 3 6 9",
        page(g, [3, 6, 9, 3, 6, 9], "e", "i", [3, 6, 9]),
        "ch 1 p",
        page(g, [1, 2, 3, 4, 5, 6], "e"),
        "qry", "prd ge 0 5", "prj 1 0", "end", ""])


def _pair():
    g = 25
    d0 = [50, 63, 75]
    d1 = [0, 3, 6, 9]
    return "\n".join([
        "seg 25 20 3",
        "ch 0 d 3 50 63 75",
        page(g, [50, 63, None, 75, 50], "e", "i", d0),
        page(g, [58, 63, 63], "e", "v"),
        "ch 0 p",
        page(g, [31, 77, 44], "w"),
        page(g, [68, 52, 39], "w"),
        "ch 0 p",
        page(g, [10, None, 22, 17, None, 13], "e"),
        "ch 1 p",
        page(g, [0, 2, 4, 1, 3], "e"),
        "ch 1 p",
        page(g, [None] * 5, "e"),
        "ch 1 d 4 0 3 6 9",
        page(g, [0, 3, 6, 9, 0, 3], "e", "i", d1),
        page(g, [6, 9, 0, 3], "e", "i", d1),
        "ch 2 p",
        page(g, [104, 118, None, 137, 122, 109, None, 131, 115, 126], "w"),
        page(g, [140, 102, None, 119, 133, 107, 124, 112, 138, 128], "w"),
        "up 0 3 70", "up 0 15 44", "up 2 12 -", "up 1 7 8", "del 5", "del 17",
        "qry", "prd ge 0 40", "prd le 2 130", "prd nn 1", "prj 2 0", "end",
        "qry", "prd nu 1", "prd ne 0 63", "prj 0 1", "end",
        "qry", "prd le 0 60", "prj 1 0", "end", ""])


TINY = _tiny()
PAIR = _pair()


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
