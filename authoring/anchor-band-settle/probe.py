#!/usr/bin/env python3
"""Correct output of one program against every reading's. Never ships.

    python3 probe.py <program file | case name> [reading ...]
"""
import os
import sys

import lab
import readings

cases, gen, model = lab.sealed()


def main(argv):
    arg = argv[1]
    if os.path.isfile(arg):
        lines = open(arg).read().strip("\n").split("\n")
    else:
        lines = cases.prog(arg)
    text = "\n".join(lines) + "\n"
    want = model.expect(lines)
    naive = lab.naive().run(text)
    print("model   ", " | ".join(want), "" if naive == want else "   NAIVE DIFFERS: %s" % naive)
    names = argv[2:] or list(readings.READINGS)
    for name in names:
        got = lab.run_text(lab.tree(files=readings.build(name)), text)
        if got != want:
            print("%-20s %s" % (name, " | ".join(got)))


if __name__ == "__main__":
    main(sys.argv)
