#!/usr/bin/env python3
"""Write the sample pipelines under environment/app_src/pipes. Never ships.

`small.txt` is written by hand. `long.txt` and `deep.txt` come from the generator's two large
builders at a fixed authoring seed, so timing them measures the real shapes while the graded
instances, drawn from a seed made inside the verifier, are never shipped. Every file is checked
against the rules a pipeline file must keep, and written with LF endings.

    python3 -u authoring/restate-hold-plan/make_pipes.py [--check]
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

PIPES = lab.SRC / "pipes"

SMALL = """now 700
src raw h 1440
src fx d 1440
step clk h 36 raw
step ses h 96 clk~4 fx-1
step tot d 480 clk/d
step rev d 480 clk/d ses/d
step bal d 240 rev bal-1
step wk d 480 rev~7 tot~7
stand tot clk
pin tot 25
pin bal 22
fix raw 610
"""


def wanted():
    _cases, gen, _model = lab.sealed()
    out = {"small.txt": SMALL}
    for fam in ("long", "deep"):
        lines = gen.build(fam, random.Random("authoring-sample|" + fam))
        out[fam + ".txt"] = "\n".join(lines) + "\n"
    for text in out.values():
        gen.check(text.strip().splitlines())
        assert "\r" not in text
    return out


def main():
    want = wanted()
    if "--check" in sys.argv[1:]:
        bad = [n for n, t in want.items()
               if not (PIPES / n).is_file() or (PIPES / n).read_text(encoding="utf-8") != t]
        print("sample pipelines %s" % ("stale: %s" % bad if bad else "match"))
        return 1 if bad else 0
    PIPES.mkdir(parents=True, exist_ok=True)
    for name, text in want.items():
        (PIPES / name).write_text(text, encoding="utf-8", newline="\n")
        print("wrote %s (%d lines)" % (name, text.count("\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
