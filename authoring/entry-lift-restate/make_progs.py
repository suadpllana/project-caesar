import pathlib as _pl
import sys as _sys

_sys.path.insert(0, str(_pl.Path(__file__).resolve().parent.parent.parent
                        / "tasks" / "entry-lift-restate" / "tests"))

"""Write the four programs that ship in /app/progs.

`tiny` and `pair` are small enough to read; `wide` and `deep` are the two scale families at
the size the graded set uses, so the agent can time its own work against the limit. They are
generated from authoring seeds, never from the nonce the verifier draws, so the shipped
samples are not the graded population.

Every file is written with newline="\\n" and checked for a carriage return: a generator that
writes a shipped file without pinning the newline produces CRLF on Windows and only zipcheck
on the built archive catches it (CLAUDE.md, reach-pair-sweep).
"""

import random
import sys

import gen

OUT = _pl.Path(__file__).resolve().parent.parent.parent \
    / "tasks" / "entry-lift-restate" / "environment" / "app_src" / "progs"

TINY = [
    "set 4 10",
    "set 4 20",
    "get 0 4",
    "off 0",
    "get 0 4",
    "all",
]

PAIR = [
    "open",
    "sec 1",
    "lnk 0",
    "shut",
    "sec 0",
    "set 7 42",
    "set 9 1",
    "sec 1",
    "open",
    "cut 7",
    "shut",
    "once 9 1 add 7 5",
    "get 1 7",
    "get 1 9",
    "off 5",
    "get 1 7",
    "all",
]


def write(name, lines):
    path = OUT / ("%s.txt" % name)
    text = "\n".join(lines) + "\n"
    path.write_text(text, encoding="utf-8", newline="\n")
    assert "\r" not in path.read_text(encoding="utf-8"), "%s picked up a carriage return" % name
    print("%-5s %7d lines  %8d bytes" % (name, len(lines), path.stat().st_size), flush=True)


def main(_argv):
    OUT.mkdir(parents=True, exist_ok=True)
    write("tiny", TINY)
    write("pair", PAIR)
    for name, fn in gen.BIG:
        rng = random.Random("sample/%s" % name)
        write(name, fn(rng, gen.BIG_SIZE))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
