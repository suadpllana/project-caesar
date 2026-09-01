#!/usr/bin/env python3
"""Does the enumerated set actually separate the wrong readings a solver will have?

Per-rule coverage on paper is not coverage. `guard-mark-unwind` shipped 27 enumerated
programs, one per rule, and a probe agent passed **all 27** with a wrong reading of the
resting rule, dying only on 6 of 300 generated programs. Under all-or-nothing grading that
is indistinguishable from bad luck, and it is one of the four causes behind a 0-of-8
difficulty rejection.

The question a hand-written case set cannot answer by inspection is not "is every rule
covered" but "does a *specific* plausible-but-wrong reading survive the set". The only way
to know is to write that reading down and run it. This does that, and when the set does not
separate a reading it finds a counterexample in the generated space and shrinks it to
something short enough to ship as a case.

Three outcomes per reading, and all three are useful:

  separated    an enumerated case already fails it. The set pins that rule.
  BLIND        no enumerated case fails it, but generated programs do. The shrunk
               counterexample is printed - add it as a case, inside the sweep that names
               the rule, so a failure says which rule broke instead of "6 of 300 random
               programs wrong".
  equivalent   nothing anywhere separates it. Either it is a correct alternative
               implementation, in which case promote it to authoring/variants/ and require
               it to score 1, or your generated space is too narrow to reach it.

The task supplies `authoring/readings.py`. The contract is small:

    REFERENCE            path to the reference policy directory
    READINGS             {name: {filename: source}} - the wrong readings, as the files
                         they would replace in the reference
    run(policy, text)    drive one program under one policy directory, returning
                         something comparable with == (a trace, a token list, a tuple)
    enumerated()         [(name, program_text)] - the shipped enumerated set
    generated(n)         [(name, program_text)] - n programs from the task's generator

Usage:
    python tools/readingcheck.py <slug> [rounds]

Exit code 0 if every reading is separated by the enumerated set, 1 otherwise.
"""

from __future__ import annotations

import importlib.util
import shutil
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DEFAULT_ROUNDS = 400


def load(task: Path):
    spec_path = task / "authoring" / "readings.py"
    if not spec_path.is_file():
        return None
    sys.path.insert(0, str(task / "authoring"))
    sys.path.insert(0, str(task / "tests"))
    spec = importlib.util.spec_from_file_location("readings", spec_path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def policy_dir(mod, files: dict[str, str]) -> Path:
    """The reference with the reading's files swapped in."""
    d = Path(tempfile.mkdtemp(prefix="reading-"))
    for p in Path(mod.REFERENCE).iterdir():
        if p.suffix == ".py":
            shutil.copyfile(p, d / p.name)
    for name, src in files.items():
        (d / name).write_text(src)
    return d


def line_reductions(text: str):
    """Fallback: one fewer line at a time, last line first."""
    lines = text.split("\n")
    for i in range(len(lines) - 1, -1, -1):
        yield "\n".join(lines[:i] + lines[i + 1:])


def shrink(mod, ref, alt, text: str) -> str:
    """Greedily reduce while the two policies still disagree.

    A line-at-a-time shrinker plateaus on a bracketed language, because dropping the line
    that opens a region leaves its closer dangling and the program stops parsing. A task
    that defines `reductions(text)` in its readings.py can offer structure-aware candidates
    - drop a region with its closer, drop a whole procedure - and the counterexample comes
    out short enough to read. Without it this still works, just less well: on this task the
    line-only shrinker stopped at 109 lines where the structure-aware one reaches 9.
    """
    def differs(t: str) -> bool:
        if not t.strip():
            return False
        try:
            return mod.run(ref, t) != mod.run(alt, t)
        except Exception:
            return False

    candidates = getattr(mod, "reductions", line_reductions)
    cur = text.strip("\n")
    changed = True
    while changed:
        changed = False
        for cand in candidates(cur):
            if differs(cand):
                cur, changed = cand, True
                break
    return cur


def check(task: Path, rounds: int) -> int:
    mod = load(task)
    if mod is None:
        print("%s: no authoring/readings.py - nothing to check "
              "(see the contract in this file's docstring)" % task.name)
        return 0

    ref = Path(mod.REFERENCE)
    enumerated = list(mod.enumerated())
    generated = list(mod.generated(rounds))
    print("== %s   %d readings, %d enumerated, %d generated"
          % (task.name, len(mod.READINGS), len(enumerated), len(generated)))

    blind = 0
    for name, files in sorted(mod.READINGS.items()):
        alt = policy_dir(mod, files)
        hit = None
        for case, text in enumerated:
            try:
                if mod.run(ref, text) != mod.run(alt, text):
                    hit = case
                    break
            except Exception as exc:
                hit = "%s (raised %s)" % (case, type(exc).__name__)
                break
        if hit:
            print("   separated  %-28s by %s" % (name, hit))
            continue

        found = None
        for case, text in generated:
            try:
                if mod.run(ref, text) != mod.run(alt, text):
                    found = text
                    break
            except Exception:
                continue
        if found is None:
            print("   equivalent %-28s nothing separates it - promote it to variants/ and "
                  "require 1, or widen the generator" % name)
            continue

        blind += 1
        small = shrink(mod, ref, alt, found)
        print("   BLIND      %-28s no enumerated case fails it; %d generated programs do."
              % (name, sum(1 for _, t in generated
                           if _safe_differs(mod, ref, alt, t))))
        print("              shrunk counterexample (%d lines) - ship it as a case:"
              % len(small.split("\n")))
        for line in small.split("\n"):
            print("                  %s" % line)
    return 1 if blind else 0


def _safe_differs(mod, ref, alt, text) -> bool:
    try:
        return mod.run(ref, text) != mod.run(alt, text)
    except Exception:
        return False


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    task = REPO / "tasks" / argv[1]
    if not task.is_dir():
        print("no such task: %s" % task)
        return 2
    rounds = int(argv[2]) if len(argv) > 2 else DEFAULT_ROUNDS
    return check(task, rounds)


if __name__ == "__main__":
    sys.exit(main(sys.argv))
