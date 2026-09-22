"""Write the sample programs that ship under environment/app_src/progs.

They are inputs only - no trace, no expected output, nothing derived from a correct run.
`tiny` and `pair` are written by hand so the brief has something small to point at; `wide`
and `deep` come from the same two large families the graded set uses, so an agent can time
its work against the shapes it will actually be graded on.

Every file is written with newline="\\n" and checked for a stray carriage return, because
zipcheck is the only gate that reads a shipped .txt as text (CLAUDE.md, 2026-09-06).
"""
import sys as _sys

# Importing the bundle's own modules must not leave a __pycache__ inside
# tasks/<slug>/: authoring scratch that lands in the task folder has been packaged
# before (CLAUDE.md, token-seam-emit).
_sys.dont_write_bytecode = True

import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "feed-lag-pare")
sys.path.insert(0, os.path.join(TASK, "tests"))

import gen  # noqa: E402

TINY = """set 0 4
add 0 3
mark m
add 0 5
add 0 -5
read m 0
pare 2
"""

PAIR = """set 0 1
set 1 6
feed f 0 0
add 0 2
add 1 2
mark m
add 0 3
add 1 3
read f 0
read m 1
pare 4
close f
pare 0
"""


def put(name, text):
    where = os.path.join(TASK, "environment", "app_src", "progs", name)
    assert "\r" not in text, name
    with open(where, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("%-10s %7d bytes %6d lines" % (name, len(text), text.count("\n")))


def main():
    put("tiny.txt", TINY)
    put("pair.txt", PAIR)
    for name, fam in (("wide.txt", "wide"), ("deep.txt", "deep")):
        lines = gen.MAKERS[fam](random.Random("sample|%s" % fam))
        put(name, "\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
