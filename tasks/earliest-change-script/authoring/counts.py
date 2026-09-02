#!/usr/bin/env python3
"""How wrong each cheat is on the short blocks, counted rather than asserted.

Every figure quoted in task.toml about a cheat's answers comes from here. Run
it after any change to the rule, the case generator or a cheat; a figure in
the prose that this script no longer prints is stale.

  python3 authoring/counts.py            all cheats, seed 1 for the random block
"""

import importlib.util
import pathlib
import sys
import time

TASK = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))

import casegen  # noqa: E402
import oracle  # noqa: E402

SEED = 1
SLOW = {"table_walk.py", "split_hunks.py"}   # quadratic; skip pairs over 40 lines


def load(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def count(module, cases):
    wrong = 0
    for before, after in cases:
        try:
            got = [tuple(op) for op in module.changes(before, after)]
        except Exception:
            got = None
        if got != [tuple(op) for op in oracle.script(before, after)]:
            wrong += 1
    return wrong


def main():
    fixed = list(casegen.FIXED)
    structured = casegen.structured_cases()
    random_block = casegen.random_cases(12000, SEED)
    truth = {}
    print("%-32s %10s %10s %10s" % ("submission", "fixed", "enumerated", "random"))
    for path in sorted((TASK / "cheat").glob("*.py")) + sorted(
            (TASK / "authoring" / "variants").glob("*/change_script.py")):
        label = path.name if path.parent.name == "cheat" else "variant " + path.parent.name
        module = load(path)
        started = time.time()
        rows = [count(module, fixed), count(module, structured),
                count(module, random_block)]
        print("%-32s %10d %10d %10d   (%d, %d, %d cases, %.0fs)"
              % (label, rows[0], rows[1], rows[2], len(fixed),
                 len(structured), len(random_block), time.time() - started))
        sys.stdout.flush()


if __name__ == "__main__":
    main()
