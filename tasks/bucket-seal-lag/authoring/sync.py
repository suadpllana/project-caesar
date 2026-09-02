"""Refresh tests/pristine from environment/app_src.

The verifier compares the executed tree against this copy after the run and
derives the sealed function digests by compiling these sources, so a change in the
environment that does not land here shows up as an attestation failure on a
correct submission.
"""

import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "environment" / "app_src"
DST = ROOT / "tests" / "pristine"


def main():
    if DST.exists():
        shutil.rmtree(DST)
    shutil.copytree(SRC, DST, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    n = sum(1 for _ in DST.rglob("*") if _.is_file())
    print("pristine: %d files" % n)
    return drift()


def drift():
    """The three plans that ship in the tree are graded, so cases.py carries them
    as literals. It cannot read them from tests/pristine at run time: the verifier
    image moves that directory to /pristine while it is being built, so a path that
    resolves on the authoring host resolves nowhere in the container. This checks
    the two copies still agree."""
    sys.path.insert(0, str(ROOT / "tests"))
    import cases
    bad = 0
    for name in ("direct", "relay", "redrive"):
        want = (SRC / "plans" / (name + ".txt")).read_text()
        if cases.PLANS.get(name) != want:
            print("cases.py has drifted from plans/%s.txt" % name)
            bad += 1
    if not bad:
        print("shipped plans: 3 in step with cases.py")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
