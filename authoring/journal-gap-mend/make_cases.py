"""Write tests/seal/cases.py from the searched journals (find_cases.py, find_example.py).

Every hand journal was found by search, not written from memory: the reading cases are the
shortest journals the named wrong reading gets wrong, preferring ones no other reading gets
wrong; the fence cases are the shortest journals whose right printout has the named shape.
Identical journals found for two purposes are kept once, under the first name.

    python3 authoring/journal-gap-mend/make_cases.py <found.json> <example.json>
"""
import json
import pathlib
import sys

TASK = pathlib.Path(__file__).resolve().parents[2] / "tasks" / "journal-gap-mend"

# (name, source kind, source key, what it pins) in grading order
PLAN = [
    ("small", "example", 0,
     "the brief's worked example: a restored entry, then two candidates in text order"),
    ("beat-needs-lock", "reading", "beat-anytime",
     "only a session holding a lock can send the heartbeat the totals count"),
    ("live-candidates", "reading", "candidates-local",
     "a candidate is an entry some complete account holds, not any request the table accepts"),
    ("digest-anchored", "reading", "digest-floats",
     "a digest sits right after the grant that triggers it, which forces the release before it"),
    ("digest-on-grant", "reading", "digest-on-multiple",
     "only an entry that raises the grant total to a multiple of K writes a digest"),
    ("later-evidence", "reading", "forward-only",
     "a span with no markers of its own, settled by a digest after it (also the shipped plan)"),
    ("pass-first-waiter", "reading", "last-come-pass",
     "a pass hands the lock to the first session in its queue"),
    ("queue-order", "reading", "merge-holders",
     "three lost requests whose order only the queues in the final audit fix"),
    ("reentry-depth", "reading", "no-depth",
     "a reentry deepens the lock, which the audit's whole-table fingerprint shows"),
    ("end-of-span", "reading", "no-end",
     "one account ends the first span where another adds a release: the dash is a candidate"),
    ("pass-is-grant", "reading", "pass-uncounted",
     "a pass counts as a grant and writes the digest right after the release"),
    ("two-spans-one-beat", "reading", "single-start",
     "one heartbeat either span may hold: the second span inherits every table the first leaves"),
    ("empty-then-grant", "reading", "span-local",
     "only the final audit shows the first span held nothing"),
    ("waiter-silent", "reading", "waiting-sends",
     "a waiting session sends nothing, which orders the two lost requests"),
    ("audit-before-loss", "reading", "walk-no-closure",
     "an audit listed inside a span was taken before its first lost entry"),
    ("audits-inside", "reading", "audit-at-end",
     "two audits inside one span, each standing where its totals fit"),
    ("digest-before-gap", "fence", "digest-before-gap",
     "a digest right after the surviving entry that triggered it, then the span"),
    ("both-empty", "fence", "empty",
     "two spans every account leaves empty: the header alone, for each"),
    ("choices-first", "fence", "none",
     "accounts part at the very first entry of the span"),
    ("dash-first", "fence", "none-dash",
     "the end of a span as a candidate, sorted before every entry"),
    ("restored-then-choice", "fence", "partial",
     "an entry every account agrees on, then a choice"),
    ("restored-then-dash", "fence", "partial-dash",
     "an entry every account agrees on, then a choice that includes the end"),
    ("kinds-in-order", "fence", "text-order",
     "candidates of three kinds, sorted as text"),
    ("three-spans", "fence", "three-spans",
     "spans numbered from 1: one restored, one empty, one restored"),
]


def main(argv):
    found = json.loads(pathlib.Path(argv[0]).read_text(encoding="utf-8"))
    example = json.loads(pathlib.Path(argv[1]).read_text(encoding="utf-8"))
    seen = {}
    rows = []
    for name, kind, key, why in PLAN:
        if kind == "example":
            text = example[key][0]
        elif kind == "reading":
            text = found["readings"][key][0]
        else:
            text = found["fences"][key][0]
        text = text.strip("\n")
        if text in seen:
            raise SystemExit("%s repeats the journal of %s" % (name, seen[text]))
        seen[text] = name
        rows.append((name, why, text))
    out = ['"""Hand journals, one per graded decision plus the ordinary side of each fence.',
           "",
           "Root-only (tests/seal is 0700 before any submitted code runs). Every journal here",
           "was found by search over small generated journals, not written from memory; the",
           "comment above each says what it pins. Frozen answers are in gt.json.",
           '"""',
           "",
           "JOURNALS = {}",
           ""]
    for name, why, text in rows:
        out.append("# %s" % why)
        out.append("JOURNALS[%r] = \"\"\"\\" % name)
        out.extend(text.split("\n"))
        out.append('"""')
        out.append("")
    out.append("ORDER = tuple(JOURNALS)")
    out.append("")
    out.append("")
    out.append("def text(name):")
    out.append("    return JOURNALS[name]")
    path = TASK / "tests" / "seal" / "cases.py"
    path.write_text("\n".join(out) + "\n", encoding="utf-8", newline="\n")
    print("cases.py: %d hand journals" % len(rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
