"""Write tests/gt.json from the sealed model, and refresh tests/pristine/.

Both outputs are pinned to LF and checked for stray carriage returns before being written:
a generator that leaves the platform's line ending in a shipped file is only caught by
zipcheck on the built archive, one gate too late.

    python3 authoring/grid-spread-refresh/build_gt.py
"""

import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "grid-spread-refresh")
sys.path.insert(0, os.path.join(TASK, "tests"))

import cases  # noqa: E402
import oracle  # noqa: E402


def write(path, text):
    if "\r" in text:
        raise SystemExit("%s: carriage return in generated output" % path)
    with open(path, "w", newline="\n") as fh:
        fh.write(text)


def main():
    truth = {"cases": {}}
    for name in sorted(cases.CASES):
        truth["cases"][name] = oracle.solve(cases.CASES[name])
    write(os.path.join(TASK, "tests", "gt.json"),
          json.dumps(truth, indent=1, sort_keys=True) + "\n")

    src = os.path.join(TASK, "environment", "app_src")
    dst = os.path.join(TASK, "tests", "pristine")
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for base, _, files in os.walk(dst):
        for fn in files:
            p = os.path.join(base, fn)
            with open(p, "rb") as fh:
                if b"\r" in fh.read():
                    raise SystemExit("%s: carriage return in the pristine copy" % p)

    print("gt.json: %d cases; pristine: %d files"
          % (len(truth["cases"]), sum(len(f) for _, _, f in os.walk(dst))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
