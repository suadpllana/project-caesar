#!/usr/bin/env python3
"""Is the shipped prose calibrated against the retained bundles, or copied from them?

`AGENTS.md` says to use the retained tasks as style calibration "without copying their
prose". That is a claim about the text, and nothing in this kit was looking at it:
`simcheck.py` compares the files under `environment/` and `tests/`, where near-identical
boilerplate is expected and benign. The fields the platform's similarity and AI-text screens
actually read - `instruction.md` and the four `[metadata]` prose fields - were unmeasured.

Measured on 2026-09-13, writing the metadata for `anchor-mean-settle` with a retained
`task.toml` open beside it produced 221 shared six-word runs against
`slab-fold-scope`'s `verification_explanation`, 94 against its `difficulty_explanation` and
83 against its instruction: whole sentences with one noun swapped, invisible to every other
check and clean under `simcheck`. Rewriting from the facts brought the worst figure to 4 in
the metadata and 19 in the brief.

WHAT THIS MEASURES. For each shipped prose field, the number of distinct six-word runs it
shares with the same field of every other task in `tasks/`. Six words is long enough that
domain vocabulary does not collide by accident and short enough to catch a reworded
sentence. The required closing sentence of every instruction is stripped first, since every
bundle must carry it verbatim.

WHAT THIS IS NOT. A pass/fail gate, and the reason is the calibration itself. Run with
`--all`, the retained set measures between 0 and 417: `alias-settle-report` and
`guard-mark-unwind` share 417 runs in `verification_explanation`, 57 in
`difficulty_explanation` and 27 in their briefs, and the contributor reports both as passed.
So the platform's screens plainly tolerate a shared house frame between one contributor's own
submissions, and a threshold derived from "what passed" would be no threshold at all. Any
number here is a risk signal to read and act on, never a prediction of rejection, and this
tool always exits 0.

What to do with the number is a judgement. 400 runs is a passage carried over wholesale, and
whatever the screens tolerate, the passage is not this task's. Under about 20 is the mandated
closing sentence and the vocabulary the mechanics force. In between, read the shared runs the
report prints and decide whether the sentence is yours.

Usage:
    python tools/prosecheck.py <slug>          measure one bundle against the others
    python tools/prosecheck.py <slug> --show   print the longest shared passages too
    python tools/prosecheck.py --all           every bundle against every other
"""

from __future__ import annotations

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
FIELDS = ("difficulty_explanation", "solution_explanation", "verification_explanation",
          "relevant_experience")
GRAM = 6
SHARED_FRAME = 20
CARRIED_OVER = 100
SUFFIX = re.compile(r"You have \d+ seconds to complete this task\..*$", re.S)


def prose(task: Path) -> dict[str, str]:
    out = {}
    brief = task / "instruction.md"
    if brief.is_file():
        out["instruction"] = SUFFIX.sub("", brief.read_text(encoding="utf-8"))
    cfg = task / "task.toml"
    if cfg.is_file():
        try:
            meta = tomllib.loads(cfg.read_text(encoding="utf-8")).get("metadata", {})
        except tomllib.TOMLDecodeError:
            meta = {}
        for key in FIELDS:
            if isinstance(meta.get(key), str) and meta[key].strip():
                out[key] = meta[key]
    return out


def runs(text: str) -> set[str]:
    words = re.findall(r"[a-z0-9']+", text.lower())
    return {" ".join(words[i:i + GRAM]) for i in range(len(words) - GRAM + 1)}


def compare(slug: str, others: list[str], show: bool = False) -> int:
    mine = {k: runs(v) for k, v in prose(ROOT / "tasks" / slug).items()}
    if not mine:
        print("%s: no shipped prose to measure" % slug)
        return 0
    print("== %s" % slug)
    bad = 0
    for key in ("instruction",) + FIELDS:
        if key not in mine:
            continue
        worst, who = 0, "-"
        for other in others:
            theirs = prose(ROOT / "tasks" / other).get(key)
            if not theirs:
                continue
            n = len(mine[key] & runs(theirs))
            if n > worst:
                worst, who = n, other
        tag = "the vocabulary the mechanics force"
        if worst >= CARRIED_OVER:
            tag, bad = "a passage carried over - read it", bad + 1
        elif worst >= SHARED_FRAME:
            tag = "a shared frame - read it"
        print("   %-26s %4d shared %d-word runs with %-22s %s"
              % (key, worst, GRAM, who, tag))
        if show and worst:
            theirs = prose(ROOT / "tasks" / who).get(key, "")
            for run in sorted(mine[key] & runs(theirs), key=len, reverse=True)[:3]:
                print("        %s" % run)
    return bad


def main(argv: list[str]) -> int:
    tasks = sorted(p.name for p in (ROOT / "tasks").iterdir() if (p / "task.toml").is_file())
    if len(argv) < 2:
        print(__doc__)
        return 2
    show = "--show" in argv
    if argv[1] == "--all":
        bad = sum(compare(t, [o for o in tasks if o != t], show) for t in tasks)
    else:
        if argv[1] not in tasks:
            print("no such task: %s" % argv[1])
            return 2
        bad = compare(argv[1], [o for o in tasks if o != argv[1]], show)
    print()
    print("%d field(s) carry a passage from another bundle; this is a report, not a gate"
          % bad)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
