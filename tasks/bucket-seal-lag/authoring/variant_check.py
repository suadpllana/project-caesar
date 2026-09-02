"""Every alternative correct implementation must score 1.

This is the run audit applied before the pipeline applies it. A graded quantity
that two correct implementations disagree on is an implementation choice being
graded, and the only way to find that out is to write the other implementations.
"""

import glob
import os
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "authoring"))
sys.path.insert(0, str(ROOT / "tests"))

import trial


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 150
    return trial.main(["--n", str(n), "--variants", "--nonce", "variants"])


if __name__ == "__main__":
    sys.exit(main(sys.argv))
