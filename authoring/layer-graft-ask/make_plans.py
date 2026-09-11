"""Write the two shipped scale plans from a public seed.

`wide.txt` and `deep.txt` are the same two families the graded set contains, at the same
size, so the agent can time its own service against the stated limit before it submits. They
are generated from a seed printed here rather than the nonce the verifier draws, so they are
not among the plans it is graded on.
"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "layer-graft-ask"
sys.path.insert(0, str(TASK / "tests"))

import gen  # noqa: E402

SEED = "shipped-sample-2026-09-11"
OUT = TASK / "environment" / "app_src" / "plans"


def main():
    import random
    for name, fn in gen.SCALE:
        text = fn(random.Random("%s/%s" % (SEED, name)))
        assert "\r" not in text
        path = OUT / (name + ".txt")
        with open(path, "w", encoding="utf-8", newline="\n") as fh:
            fh.write(text)
        print("%s  %d lines  %d bytes" % (path.name, text.count("\n"), len(text)))
    return 0


if __name__ == "__main__":
    sys.exit(main())
