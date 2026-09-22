"""Write the four programs that ship in /app/progs.

`tiny` is the worked example the brief quotes a line of. It was searched for, not chosen: of
4000 candidates it is among the shortest whose shipped output differs from the reference and
which decides no reading the brief leaves to derivation (pick_tiny.py). `pair` is a second
ordinary program. `wide` and `deep` are one program each of the two scale families, so the
execution limit can be timed against the sizes the brief states.
"""
import pathlib
import random
import sys

import gen_rand
import lab

sys.path.insert(0, str(lab.ROOT / "tasks" / "claim-stand-break" / "tests"))
import gen  # noqa: E402

OUT = lab.ROOT / "tasks" / "claim-stand-break" / "environment" / "app_src" / "progs"

TINY_SEED = 703076
TINY_SHAPE = (12, 6, 2, 3)
PAIR_SEED = 820067
PAIR_SHAPE = (30, 9, 3, 3)


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    text = gen_rand.program(TINY_SEED, *TINY_SHAPE)
    (OUT / "tiny.txt").write_text(text, encoding="utf-8", newline="\n")
    (OUT / "pair.txt").write_text(gen_rand.program(PAIR_SEED, *PAIR_SHAPE),
                                  encoding="utf-8", newline="\n")
    for fam, name in (("wide", "wide.txt"), ("deep", "deep.txt")):
        lines = gen.MAKERS[fam](random.Random("ship|%s" % fam))
        (OUT / name).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    for one in sorted(OUT.iterdir()):
        print("%-10s %6d ops" % (one.name, len(one.read_text().splitlines())))


if __name__ == "__main__":
    main()
