#!/usr/bin/env python3
"""Write the sample programs shipped in environment/app_src/progs. Never ships.

`tiny.txt` is written by hand so that its one quoted line differs between the shipped resolver
and the rules only in the order of an ambiguity's candidates - a convention, which the brief
may give away freely - and in nothing load-bearing. The others are drawn from the verifier's
own family builders at a fixed authoring seed, so they have the graded shapes without being any
program the run will be graded on (graded seeds are 32 hex digits drawn at verification time).

    python3 -u authoring/glob-route-hide/make_progs.py
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

OUT = lab.SRC / "progs"

TINY = """flags lite
mod log
pub item emit
pub item flush
item buf if !lite
mod log.file
use log::*
pub use log::flush as sync
ref buf
mod net
pub item emit
item dial
pub use log::*
mod net.tcp
use net::*
ref dial
ref sync
mod app
use net::*
use log::*
use log.file::*
ref emit
ref flush
ref sync
ref dial
"""

AUTHOR_SEED = "authoring-samples"


def main():
    _cases, gen, _model = lab.sealed()
    OUT.mkdir(parents=True, exist_ok=True)
    wrote = {"tiny.txt": TINY}
    for fam, fname in (("nest", "nest.txt"), ("ring", "ring.txt"), ("hide", "hide.txt")):
        rng = random.Random("%s:%s" % (AUTHOR_SEED, fam))
        wrote[fname] = "\n".join(gen.SMALL[fam](rng)) + "\n"
    for fam, fname in (("tree", "tree.txt"), ("mesh", "mesh.txt")):
        rng = random.Random("%s:%s" % (AUTHOR_SEED, fam))
        wrote[fname] = "\n".join(gen.LARGE[fam](rng)) + "\n"
    for fname, text in wrote.items():
        assert "\r" not in text
        (OUT / fname).write_text(text, encoding="utf-8", newline="\n")
        print("%s: %d lines" % (fname, text.count("\n")))


if __name__ == "__main__":
    main()
