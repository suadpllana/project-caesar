"""Rebuild the mechanically renamed correct variant from the reference.

The point of `ok-renamed` is that naming is not graded, so the rename has to actually fire:
a substitution that matches nothing would ship the reference under a different directory and
pass for the wrong reason. Every rule below asserts its own count and the run fails on zero.
Names the pristine tree calls into, and the attributes it reads, are never touched.

Usage:
    python3 make_variants.py
"""
import pathlib
import re
import sys

import harness

OUT = pathlib.Path(__file__).resolve().parent / "variants" / "ok-renamed"

# left alone: cost, srcs, out_all, out_one, settle, run (called by the tree) and every name
# imported from prog.deck / prog.unit, plus the Unit attributes the rules read.
RENAMES = (
    ("deck", "tbl"),
    ("prog", "pgm"),
    ("rs", "hop"),
    ("rv", "held"),
    ("vn", "from_"),
    ("what", "want"),
    ("cands", "lot"),
    ("head", "lead"),
    ("got", "bag"),
    ("fresh", "batch"),
    ("rank", "price"),
    ("done", "settled"),
    ("owned", "here"),
    ("pulled", "carried"),
)

# `prog` and `deck` are also module names in the imports; those lines are rebuilt by hand.
KEEP_IMPORTS = {
    "step.py": "from prog.deck import UNIT, at\nfrom prog.unit import find\n",
    "show.py": "from prog.deck import CLASH, at, row\nfrom prog.unit import find\n",
    "pick.py": "from prog.deck import CLASH\n",
    "turn.py": ("from prog.deck import OWN, UNIT, at, blank, put\n"
                "from prog.unit import find\n"
                "\n"
                "from .pick import settle\n"
                "from .show import out_all, out_one\n"
                "from .step import cost, srcs\n"),
}


def rewrite(name, text):
    head = KEEP_IMPORTS[name]
    if not text.startswith(head):
        raise SystemExit("%s: import block is not what make_variants expects" % name)
    body = text[len(head):]
    fired = 0
    for old, new in RENAMES:
        body, n = re.subn(r"(?<![\w.])%s(?![\w])" % re.escape(old), new, body)
        fired += n
    if fired == 0:
        raise SystemExit("%s: no identifier was renamed - the variant would ship the "
                         "reference under another name" % name)
    return head + body, fired


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    total = 0
    for name in harness.PARTS:
        text = (harness.REF / name).read_text(encoding="utf-8")
        body, fired = rewrite(name, text)
        if body == text:
            raise SystemExit("%s: rename changed nothing" % name)
        (OUT / name).write_text(body, encoding="utf-8", newline="\n")
        print("%-10s %3d identifier(s) renamed" % (name, fired), flush=True)
        total += fired
    print("total %d" % total, flush=True)
    return 0 if total else 1


if __name__ == "__main__":
    sys.exit(main())
