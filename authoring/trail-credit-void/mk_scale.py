"""Write the two wide trails that ship in the tree, from the verifier's own generator.

The brief states the size of each of them, and the graded set is three trails of each of those
two sizes. If this file carried its own copy of the shapes, a change to `tests/gen.py` would
leave the shipped examples and the sentence in the brief describing something the graded set no
longer is - the two-tools-disagree failure this repository keeps recording. So it imports `gen`
and calls the same makers the verifier calls.

Writes with an explicit newline and asserts no carriage return survives, because a generator
that lets the platform pick the line ending ships a file only zipcheck can catch (CLAUDE.md,
2026-09-07).

    python mk_scale.py                  into the shipped tree
    python mk_scale.py <somewhere>      elsewhere, for timing
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "trail-credit-void"
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402

SHIPPED = {"wide.txt": ("wide", "shipped-wide"), "deep.txt": ("deep", "shipped-deep")}


def write(path, lines):
    body = "\n".join(lines) + "\n"
    assert "\r" not in body
    pathlib.Path(path).write_text(body, encoding="utf-8", newline="\n")


def main():
    where = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 \
        else TASK / "environment" / "app_src" / "trails"
    where.mkdir(parents=True, exist_ok=True)
    for name, (fam, seed) in SHIPPED.items():
        write(where / name, gen.MAKERS[fam](random.Random(seed)))
        one = where / name
        print("%s %d bytes, %d lines" % (name, one.stat().st_size,
                                         sum(1 for _ in one.open())), flush=True)


if __name__ == "__main__":
    main()
