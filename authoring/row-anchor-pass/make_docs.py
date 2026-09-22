#!/usr/bin/env python3
"""Write the four sample documents that ship in /app/docs. Never ships.

Two small ones the brief points at, and one of each scale family so the agent can time its
own pane against the limit. The scale pair is built by the shipped generator's own shapes with
a fixed seed, so what the agent times is the shape it is graded on rather than a guess at it.

    python3 -u authoring/row-anchor-pass/make_docs.py
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import gen  # noqa: E402

DOCS = lab.SRC / "evs"

TINY = [
    "cfg 60 1 4",
    "g 1 18 7 7 7 4",
    "g 2 18 7 26 26 5",
    "g 3 12 7 7 7 4",
    "scroll 30",
    "scroll 22",
    "scroll 9",
    "scroll -14",
    "go 0",
]

PAIR = [
    "cfg 45 1 4",
    "g 1 10 6 24 24 8",
    "g 2 22 6 6 6 3",
    "g 3 10 6 24 24 8",
    "go 70",
    "ins 1 2 3",
    "scroll 40",
    "del 1 1 4",
    "go 4000",
    "scroll -1",
    "ins 3 8 2",
    "size 120",
]


def write(name, lines):
    path = DOCS / name
    text = "\n".join(lines) + "\n"
    assert "\r" not in text
    path.write_text(text, encoding="utf-8", newline="\n")
    print("%-10s %6d lines" % (name, len(lines)))


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    write("tiny.txt", TINY)
    write("pair.txt", PAIR)
    write("wide.txt", gen.wide(random.Random("sample-wide")))
    write("deep.txt", gen.deep(random.Random("sample-deep")))


if __name__ == "__main__":
    main()
