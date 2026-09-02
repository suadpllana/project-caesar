#!/usr/bin/env python3
"""Did the BRIEF hand the solver its plan? Answered from the solver's own words.

The easiness probe tells you a task was solved. It never tells you why, and CLAUDE.md
records three rounds across two tasks spent repairing the wrong thing because the repair
was chosen from the score. This is the diagnostic that makes the choice mechanical.

THE IDEA. When a probe supplies a trajectory, the solving agent explains how it got its
plan. If that explanation reuses distinctive phrases from the instruction, the instruction
is where the plan came from - the agent is quoting you back to yourself. That is the
cheapest and most certain leak evidence there is, and it points at the exact sentences to
delete rather than at a general worry about the brief being too helpful.

Measured on `share-register-screen`, which the probe solved 3 of 3 on 2026-09-02 and which
came back 0 of 3 after the sentences this check names were removed:

    rejected brief   1 shared phrase of 8 content words, in the sentence that states the rule
    repaired brief   nothing above the floor

WHAT IT DOES NOT TELL YOU. Silence here is not "the task is hard". It rules out one of the
three easiness failure modes and leaves the other two, which live in the environment and in
the shape of the specification rather than in the prose. See "Fixing a task that the
easiness probe solved: the three failure modes" in CLAUDE.md for what to do next in each
case.

Usage:
    python3 tools/leakcheck.py <slug> <trajectory.md> [<trajectory.md> ...]
    python3 tools/leakcheck.py <slug> --self      compare the brief against itself (sanity)

Exit code 1 if the brief and the trajectory share a distinctive phrase, 0 otherwise.
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Phrase length, in words, at which shared wording stops being coincidence. Four content
# words in the same order is not two people describing one domain; it is a quotation.
MIN_N = 5
MAX_N = 14
MIN_CONTENT = 4

STOP = set("""a an and are as at be been but by can could did do does for from had has have
he her his how i if in into is it its may me more most must no nor not of off on once one
only or other our out over own same she should so some such than that the their them then
there these they this those through to too under until up very was we were what when where
which while who whom why will with would you your it's is not do not""".split())

# Paths, filenames and bare identifiers are shared by construction: the brief names the
# files and the solver talks about them. They are not evidence of anything.
TOKENISH = re.compile(r"[/\\.]|_|^[a-z]+\d+$")


def words(text: str) -> list:
    text = re.sub(r"`[^`]*`", " ", text)          # backticked paths are not prose
    text = re.sub(r"^\s{4,}.*$", " ", text, flags=re.M)   # indented samples
    return [w for w in re.findall(r"[A-Za-z']+", text.lower())]


def content(gram: tuple) -> int:
    return sum(1 for w in gram if w not in STOP and not TOKENISH.search(w))


def grams(ws: list, n: int) -> set:
    return {tuple(ws[i:i + n]) for i in range(len(ws) - n + 1)}


def sentences(text: str) -> list:
    flat = re.sub(r"\s+", " ", re.sub(r"`", "", text))
    return [s.strip() for s in re.split(r"(?<=[.!?]) ", flat) if s.strip()]


def shared(brief: str, traj: str) -> list:
    a, b = words(brief), words(traj)
    hits = []
    for n in range(MAX_N, MIN_N - 1, -1):
        for g in grams(a, n) & grams(b, n):
            if content(g) < MIN_CONTENT:
                continue
            phrase = " ".join(g)
            if any(phrase in longer for longer, _ in hits):
                continue
            hits.append((phrase, content(g)))
    return hits


def main(argv: list) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    slug = argv[1]
    brief_path = ROOT / "tasks" / slug / "instruction.md"
    if not brief_path.is_file():
        print("no instruction at %s" % brief_path)
        return 2
    brief = brief_path.read_text(encoding="utf-8")

    print("== %s" % slug)
    worst = 0
    for arg in argv[2:]:
        traj = brief if arg == "--self" else Path(arg).read_text(encoding="utf-8")
        hits = shared(brief, traj)
        label = "the brief itself" if arg == "--self" else arg
        if not hits:
            print("   %s: nothing above the floor" % label)
            continue
        worst = max(worst, len(hits))
        print("   %s: %d distinctive phrase(s) the solver reuses" % (label, len(hits)))
        for phrase, n in sorted(hits, key=lambda h: -len(h[0]))[:8]:
            print("      %d content words: %r" % (n, phrase))
            for s in sentences(brief):
                if phrase in " ".join(words(s)):
                    print("         brief: %s" % s[:150])
                    break
    print()
    if worst:
        print("   The brief is where the plan came from. Delete the sentences named above;")
        print("   that is the repair with the largest measured effect and the cheapest one.")
        return 1
    print("   The brief did not supply the wording. This rules out the brief and leaves the")
    print("   environment and the shape of the specification - see the four failure modes.")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
