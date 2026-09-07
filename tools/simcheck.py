#!/usr/bin/env python3
"""Would the similarity screen call this a variant of earlier work?

A prior submission was rejected by the similarity screen with every local gate green,
because no local gate measured the axis that rejected it. This is that gate.

It reports two things, because the rejection had two causes and only the second one is
obvious.

MECHANICAL. File-for-file sequence similarity against every other bundle in tasks/. Reusing
the harness architecture is right; shipping it as the same bytes is what makes two
submissions look like one task with the nouns changed. `reap.py` and `environment/Dockerfile`
were byte-identical across two submissions when this was written.

CONCEPTUAL, and it is the one that matters. What does the task GRADE? Four submitted tasks
here grade work counters against an unpublished budget and ship the correct-outputs-wrong-work
signature. The domain moved every time - ML, then databases, then storage engines - and the
question never did. A new task that grades the same kind of thing is a reskin however new its
subject matter is, which is what docs/RULES.md says in as many words.

Thresholds were set from the one measured rejection and the passing bundles around it, so
treat them as a hypothesis rather than as a proof: this reports "not yet similar in a way we
have already been rejected for", never "will pass".

Usage:
    python3 tools/simcheck.py <slug>
"""

from __future__ import annotations

import difflib
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Files whose near-identity across two bundles is what a mechanical screen sees.
PLUMBING = (
    "tests/reap.py",
    "tests/test.sh",
    "tests/Dockerfile",
    "tests/runner.py",
    "tests/test_outputs.py",
    "environment/Dockerfile",
    "instruction.md",
)

# Measured on 2026-08-15: the rejected bundle sat at 1.000 on two files and above 0.83 on two
# more. Bundles that passed have never been compared, so this is the rejected side only.
NEAR = 0.75
HIGH = 0.55

# The graded artifact, read off the task's own contract. A task that grades what an earlier
# one graded is the reskin the screen is looking for.
IDIOM = {
    "work-counter budget": (
        r"\b(budget|ceiling)\b.{0,120}\b(counter|folds|scans|reads|writes|probes)\b",
        r"\bover the budget\b",
    ),
    "correct-outputs-wrong-work": (
        r"correct on every (value|read|scenario).{0,80}\b(over|wrong)\b",
        r"publishes every (value|read).{0,60}wrong",
    ),
}


def text(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""


def mechanical(task: Path, others: list[Path]) -> list[str]:
    out = []
    for other in others:
        for rel in PLUMBING:
            a, b = task / rel, other / rel
            if not (a.is_file() and b.is_file()):
                continue
            r = difflib.SequenceMatcher(None, text(a), text(b)).ratio()
            if r >= NEAR:
                out.append("NEAR  %-24s %.3f against %s - rewrite it, do not copy it"
                           % (rel, r, other.name))
            elif r >= HIGH:
                out.append("HIGH  %-24s %.3f against %s" % (rel, r, other.name))
    return out


# The mandated closing sentence is identical in every brief by rule, so it is the one run
# of shared words that is not a finding.
SUFFIX = ("you have seconds to complete this task do not cheat by using online solutions "
          "or hints specific to this task")
PHRASE = 6


def words(s: str) -> list[str]:
    return re.findall(r"[a-z']+", s.lower())


def borrowed(task: Path, others: list[Path]) -> list[str]:
    """Runs of six words the brief shares with an earlier brief.

    Measured on 2026-09-07: a draft that textcheck reported as irregular enough on every
    axis still carried whole clauses out of two retained briefs, because calibrating style
    against accepted work slides into reusing its sentences. Cadence metrics cannot see
    that; this can.

    Reported, not failed. Measured across the bundles present the same day, every earlier
    brief shares runs with some other one, and the worst pair - guard-mark-unwind against
    token-seam-emit - shares 98 of them, so a threshold here would reject work the screen
    has already accepted. Read the runs it prints and decide: a shared clause of ordinary
    plumbing is different from a shared sentence that carries the brief's voice.
    """
    mine = words(text(task / "instruction.md"))
    if len(mine) <= PHRASE:
        return []
    out = []
    for other in others:
        theirs = words(text(other / "instruction.md"))
        seen = set(tuple(theirs[i:i + PHRASE]) for i in range(len(theirs) - PHRASE + 1))
        hits = sorted(set(" ".join(mine[i:i + PHRASE])
                          for i in range(len(mine) - PHRASE + 1)
                          if tuple(mine[i:i + PHRASE]) in seen))
        hits = [h for h in hits if h not in SUFFIX]
        if hits:
            out.append("BORROWED from %s: %d run(s) of %d words, e.g. \"%s\""
                       % (other.name, len(hits), PHRASE, hits[0]))
    return out


def graded(task: Path) -> set[str]:
    body = text(task / "task.toml").lower() + text(task / "instruction.md").lower()
    hit = set()
    for name, pats in IDIOM.items():
        if any(re.search(p, body, re.S) for p in pats):
            hit.add(name)
    return hit


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    task = ROOT / "tasks" / argv[1]
    if not task.is_dir():
        print("no such task: %s" % task)
        return 2
    others = [d for d in sorted((ROOT / "tasks").iterdir())
              if d.is_dir() and d.name != argv[1] and (d / "task.toml").is_file()]

    print("== %s" % argv[1])
    findings = mechanical(task, others)
    for f in findings:
        print("   " + f)
    if not findings:
        print("   mechanical: no shipped file is close to another bundle's")

    lifted = borrowed(task, others)
    for f in lifted:
        print("   " + f)
    if lifted:
        print("   Read those runs before packaging. Style calibration is not permission to")
        print("   reuse sentences; earlier briefs share up to 98 runs with each other, so")
        print("   this is a prompt to look rather than a threshold to clear.")
    else:
        print("   prose: the brief shares no six-word run with an earlier brief")

    mine = graded(task)
    shared = []
    for other in others:
        both = mine & graded(other)
        if both:
            shared.append("%s (%s)" % (other.name, ", ".join(sorted(both))))
    print()
    if shared:
        print("   GRADES WHAT %d EARLIER TASKS GRADE: %s" % (len(shared), "; ".join(shared)))
        print("   The subject matter being new does not make the task new. Change what is")
        print("   graded, not what it is about.")
    else:
        print("   conceptual: this task does not grade what any earlier one grades")

    bad = [f for f in findings if f.startswith("NEAR")]
    return 1 if (bad or len(shared) >= 2) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
