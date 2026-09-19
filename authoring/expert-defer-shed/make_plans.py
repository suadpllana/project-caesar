#!/usr/bin/env python3
"""Write the four step files that ship under /app/plans. Never ships itself.

tiny and pair are written here by hand; wide and deep come from the generator at a fixed
authoring seed so the agent can time the real shapes rather than a guess at them. Every file
is written with an explicit newline and checked for a carriage return, because a generator
that leaves the newline to the platform has put CRLF into a shipped file before.

    python3 -u authoring/expert-defer-shed/make_plans.py
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

PLANS = lab.SRC / "plans"

TINY = """cfg 4 2 600 100 75
step
mb
t 500 300 150 50
t 450 400 100 50
mb
t 600 200 150 50
t 100 100 400 400
"""

PAIR = """cfg 6 3 600 60 40
step
mb
t 250 200 180 60 40 30
t 240 210 170 70 50 20
t 700 30 20 10 5 5
mb
t 900 10 10 10 10 10
t 20 880 20 10 10 10
t 300 290 100 50 40 30
mb
t 100 95 90 85 80 75
t 850 20 20 20 20 20
step
mb
t 400 300 120 60 40 30
t 380 320 110 70 50 20
mb
t 950 10 10 10 10 10
t 340 330 90 60 50 40
"""


def put(name, text):
    assert "\r" not in text
    (PLANS / name).write_text(text, encoding="utf-8", newline="\n")
    tokens = sum(1 for line in text.splitlines() if line.startswith("t "))
    print("%-10s %d tokens, %d lines" % (name, tokens, len(text.splitlines())))


def main():
    _cases, gen, _model = lab.sealed()
    PLANS.mkdir(parents=True, exist_ok=True)
    put("tiny.txt", TINY)
    put("pair.txt", PAIR)
    for fam in ("wide", "deep"):
        rng = random.Random("plans|%s" % fam)
        put("%s.txt" % fam, "\n".join(gen.build(fam, rng)) + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
