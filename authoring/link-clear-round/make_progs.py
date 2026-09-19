#!/usr/bin/env python3
"""Write the shipped sample programs that are generated rather than hand written. Never ships.

`tiny.txt`, `pair.txt` and `deep.txt` are written by hand and live in the tree. `wide.txt` is
the store at the scale the brief states, so the agent can time its own keeper against the
limit without having to build the file first. It is drawn from a seed of its own, so it is
the same shape as the graded wide families and none of their contents.

    python3 -u authoring/link-clear-round/make_progs.py
"""
import random
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import gen  # noqa: E402


def main():
    dest = lab.SRC / "progs" / "wide.txt"
    lines = gen.build("wideout", random.Random("sample|wide|0"))
    text = "\n".join(lines) + "\n"
    assert "\r" not in text
    dest.write_text(text, encoding="utf-8", newline="\n")
    print("wrote %s: %d lines, %.1f MB" % (dest.name, len(lines), len(text) / 1e6))
    return 0


if __name__ == "__main__":
    sys.exit(main())
