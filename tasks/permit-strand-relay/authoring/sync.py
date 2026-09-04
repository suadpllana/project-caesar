"""Hold the three shipped case files equal to their copies in tests/cases.py,
and refresh tests/pristine from the tree the agent lands in.

The case files have to be literals in cases.py rather than read off the shipped
tree, because the verifier image moves pristine out of tests/ at build time and
a case set that reads a path finds nothing there. Writing both copies from one
source is what stops them drifting.
"""

import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tests"))

import cases

SHIPPED = ("strand", "handover", "lull")


def main():
    home = os.path.join(ROOT, "environment", "app_src", "cases")
    if not os.path.isdir(home):
        os.makedirs(home)
    for name in SHIPPED:
        body = json.dumps(cases.SETS[name], sort_keys=True, indent=1)
        with open(os.path.join(home, name + ".json"), "w", newline="\n") as fh:
            fh.write(body + "\n")
    pristine = os.path.join(ROOT, "tests", "pristine")
    shutil.rmtree(pristine, ignore_errors=True)
    shutil.copytree(os.path.join(ROOT, "environment", "app_src"), pristine,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    count = sum(len(f) for _, _, f in os.walk(pristine))
    print("wrote %d case files, refreshed pristine (%d files)"
          % (len(SHIPPED), count))


if __name__ == "__main__":
    main()
