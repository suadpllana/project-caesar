"""Write the graded programs to disk, as root, before any submitted code runs.

The worker only ever reads these files; it never sees the seed. The directory is root-owned and
read-only to everyone else, so the submission cannot rewrite the exam it is marked against, and
the grader does not trust this copy anyway: it regenerates every program from the seed and
checks the worker's attested digest of each one.

    python3 /tests/exam.py --seed <hex> --per <n> --out /exam
"""
import argparse
import hashlib
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import cases  # noqa: E402
import gen  # noqa: E402


def digest(lines):
    return hashlib.sha256("\n".join(lines).encode("utf-8")).hexdigest()


def everything(seed, per):
    """Every graded program as (family, name, lines): hand cases first, then the generated."""
    work = [("hand", name, cases.prog(name)) for name in cases.ORDER]
    work += gen.programs(seed, per)
    return work


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--seed", required=True)
    ap.add_argument("--per", type=int, required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args()
    index = []
    for fam, name, lines in everything(args.seed, args.per):
        fname = name + ".txt"
        with open(os.path.join(args.out, fname), "w", encoding="utf-8", newline="\n") as fh:
            fh.write("\n".join(lines) + "\n")
        index.append({"fam": fam, "name": name, "file": fname})
    with open(os.path.join(args.out, "index.json"), "w", encoding="utf-8", newline="\n") as fh:
        json.dump(index, fh)
    print("exam: %d programs" % len(index))


if __name__ == "__main__":
    main()
