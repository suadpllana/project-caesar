"""Write the four programs that ship in /app/plans.

tiny and pair are small enough to read; wide and deep are the two scale families at exactly
the size the graded set uses, so timing them locally measures what the limit measures.
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "pin-drift-redo"
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402

OUT = TASK / "environment" / "app_src" / "plans"

TINY = ["cfg 4", "tx 1", "tx 2", "add 1 0 5", "put 2 0 100", "fin 2", "fin 1"]

PAIR = [
    "cfg 6",
    "tx 1",
    "add 1 0 4",
    "cpy 1 1 0",
    "rd 1 2",
    "mk 1",
    "put 1 3 9",
    "chk 1 3 9",
    "tx 2",
    "put 2 0 30",
    "add 2 2 7",
    "fin 2",
    "raw 1 4 0",
    "bmp 1 1 3 2",
    "lim 1 1 40",
    "put 1 5 1",
    "fin 1",
]


def write(name, lines):
    body = "\n".join(lines) + "\n"
    assert "\r" not in body
    with open(OUT / name, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(body)
    print("%-10s %7d lines" % (name, len(lines)))


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    write("tiny.txt", TINY)
    write("pair.txt", PAIR)
    write("wide.txt", gen.build_wide(random.Random("plans|wide")))
    write("deep.txt", gen.build_deep(random.Random("plans|deep")))


if __name__ == "__main__":
    main()
