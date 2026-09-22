#!/usr/bin/env python3
"""Write the sample programs that ship in environment/app_src/progs. Never ships.

`long.txt` and `wide.txt` come from the graded scale builders at a fixed authoring seed, so
timing them measures the real shapes without handing over a program the run is graded on (the
graded ones are drawn from a seed chosen after the agent has finished). `small.txt` is chosen
by `pick_small.py` so that the one line the brief quotes separates the shipped plan and nothing
else.

    python3 make_progs.py
"""
import random

import lab

_cases, gen, _model = lab.sealed()
OUT = lab.SRC / "progs"


def write(name, lines):
    text = "\n".join(lines) + "\n"
    assert "\r" not in text
    (OUT / name).write_text(text, encoding="utf-8", newline="\n")
    print("%s: %d lines" % (name, len(lines)))


def main():
    OUT.mkdir(exist_ok=True)
    for kind in ("long", "wide"):
        write("%s.txt" % kind, gen.fam_big(kind, random.Random("shipped|%s" % kind)))


if __name__ == "__main__":
    main()
