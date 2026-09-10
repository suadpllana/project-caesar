"""Write the example programs that ship in /app/progs.

The two small ones are literal. The two big ones come from the same shapes the graded families
use, under a seed of their own, so the agent can time the real scale without being handed a
graded program. Every file is written with LF and checked for a stray carriage return, because
only zipcheck reads the built archive and by then the mistake is expensive.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "slab-fold-scope"
sys.path.insert(0, str(TASK / "tests"))
import gen  # noqa: E402

TINY = """
plan a
put a v 0 9
push a
plan b
cut b v 5 24
push b
"""

PAIR = """
plan a
put a v 0 9
push a
plan b
put b v 20 29
push b
plan c
fold c v 0 99
push c
at v 5
at v 15
rows v
"""


def write(name, lines):
    dest = TASK / "environment" / "app_src" / "progs" / name
    text = "\n".join(lines) + "\n"
    assert "\r" not in text, name
    dest.write_text(text, encoding="utf-8", newline="\n")
    print("%-10s %6d lines %7d bytes" % (name, len(lines), dest.stat().st_size))


def main():
    write("tiny.txt", [x for x in TINY.strip().splitlines() if x.strip()])
    write("pair.txt", [x for x in PAIR.strip().splitlines() if x.strip()])
    write("wide.txt", gen.one("wide", "example/wide"))
    write("deep.txt", gen.one("deep", "example/deep"))


if __name__ == "__main__":
    main()
