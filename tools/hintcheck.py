"""Instruction leak and staleness check.

Two failure modes, both of which reached the pipeline as an "instruction concision"
rejection on delta-view-retraction (2026-08-13):

1. The brief names a rule the cheat suite exists to catch and then refutes it
   ("the cheap test is X. It is not the line."). That hands over the discrimination
   the task is built on. Detected as a sentence structure - see REFUTATION below for
   why matching cheat-rationale vocabulary was tried first and does not work.

2. The brief quotes a work-counter figure that no longer matches tests/gt.json,
   because the reference changed and nobody re-derived the numbers.

Usage:
    python3 tools/hintcheck.py <slug>
"""

import json
import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent

def prose(text):
    """The instruction minus indented code samples, lowercased."""
    out = []
    for line in text.splitlines():
        if line.startswith("    ") or line.startswith("\t"):
            continue
        out.append(line)
    return "\n".join(out).lower()


# A brief pre-eliminates a candidate rule by naming it and then declaring it wrong.
# That is a structure, not a vocabulary: two measurements on the same subject can share
# every domain word and only one of them refutes anything. Matching cheat rationale
# terms was tried first and abandoned - several cheats embed the reference commentary,
# so they share forty-odd ordinary words with any brief about this engine and the check
# fired on all of them.
REFUTATION = (
    re.compile(r"\bit is not the (line|test|rule|answer|distinction|condition)\b"),
    re.compile(r"\bthat (is|reading) (is )?(not|never) (it|the|right|enough|correct)\b"),
    # "first" is dropped deliberately: it is ordinal far more often than dismissive,
    # and "to check the first answer" in turn-seam-alignment is a cost constraint the
    # solver needs, not a rule being refuted.
    re.compile(r"\bthe (cheap|obvious|naive|tempting|easy) (test|rule|reading|"
               r"answer|plan|guess|move)\b"),
    re.compile(r"\b(looks like|seems like|reads as) the .{0,40}\band it is not\b"),
    re.compile(r"\bis (wrong|not right|not the line)\b[^.]{0,60}\bbecause\b"),
    re.compile(r"\bdo(es)? not work\b[^.]{0,40}\bbecause\b"),
)


# A brief that tells the solver where the difficulty is has handed over the plan, however
# carefully it avoids naming the rule. `share-register-screen` failed the easiness probe
# 3 of 3 on 2026-09-02 carrying "What those holdings come to at a meeting is the whole of
# what the screen has to get right", written in the belief that it stated the input space.
# It does not: it names the quantity the task is built on and says that quantity is the
# answer. The solving trajectory reached the rule in its first message, in those words.
#
# These are thesis sentences about the work rather than requirements on the output. A
# requirement says what must be true of the answer; one of these says which part of the
# problem to think about.
EMPHASIS = (
    # Narrowed deliberately. rollout-cache-coherence, which passed the screen, carries
    # "what it has computed is the whole of what is at stake for it" - a statement about a
    # request in the domain, not about the solver's job. The leak is the form that names
    # the solver or its program as the thing that must get the quantity right.
    re.compile(r"\bis the whole of what\b[^.]{0,60}\b(get|getting) (it )?right\b"),
    re.compile(r"\bthe whole of (the|what) (work|task|difficulty|problem|thing)\b"),
    re.compile(r"\bwhat (you|we|the \w+) (have|has) to get right\b"),
    re.compile(r"\bis where the (task|difficulty|work|problem) (lives|is)\b"),
    re.compile(r"\bthe (key|crux|heart|nub) of (it|this|the \w+) is\b"),
    re.compile(r"\bthat is the whole (task|point|game|of it)\b"),
    re.compile(r"\ball (that|of) (this|it) turns on\b"),
)


def check_emphasis(text):
    """Flag sentences that point at the part of the problem that carries the difficulty."""
    findings = []
    for sentence in re.split(r"(?<=[.!?])\s+", prose(text)):
        s = " ".join(sentence.split())
        for pat in EMPHASIS:
            if pat.search(s):
                findings.append(
                    "emphasis: %r - naming the quantity the task is built on and saying it "
                    "is what must be got right hands over the plan, whatever else the "
                    "sentence withholds" % s[:110]
                )
                break
    return findings


def check_hints(text):
    """Flag sentences that name a candidate rule and refute it.

    Stating a wrong rule so the solver need not discover it is wrong hands over the
    discrimination the cheat suite exists to measure. This is what the concision
    reviewer caught on delta-view-retraction: "The cheap test is that the multiplicity
    folded exceeds the candidates kept. It is not the line."
    """
    findings = []
    body = prose(text)
    for sentence in re.split(r"(?<=[.!?])\s+", body):
        s = " ".join(sentence.split())
        for pat in REFUTATION:
            if pat.search(s):
                findings.append(
                    "refutation: %r - naming a rule and rejecting it pre-eliminates a "
                    "candidate the solver should have to test" % s[:110]
                )
                break
    return findings


def check_numbers(slug, text):
    """Every 'N folds' / 'N scans' in the brief must exist in gt.json."""
    findings = []
    gtp = ROOT / "tasks" / slug / "tests" / "gt.json"
    if not gtp.is_file():
        return findings
    gt = json.loads(gtp.read_text(encoding="utf-8"))
    scen = gt.get("scenarios", {})

    known = {"folds": set(), "scans": set()}
    for rec in scen.values():
        for field in ("folds", "scans"):
            if field in rec:
                known[field].add(rec[field])
        for field in ("shipped_folds", "shipped_scans"):
            if field in rec:
                known[field.split("_", 1)[1]].add(rec[field])

    for m in re.finditer(r"(\d+)\s+(folds|scans)", prose(text)):
        n, field = int(m.group(1)), m.group(2)
        if n not in known[field]:
            findings.append(
                "instruction claims %d %s, which appears nowhere in tests/gt.json "
                "(known %s: %s)"
                % (n, field, field, ", ".join(str(x) for x in sorted(known[field])))
            )
    return findings


def main():
    if len(sys.argv) != 2:
        print(__doc__.strip())
        return 2
    slug = sys.argv[1]
    ip = ROOT / "tasks" / slug / "instruction.md"
    if not ip.is_file():
        print("no instruction at %s" % ip)
        return 2
    text = ip.read_text(encoding="utf-8")

    print("== %s" % ip)
    findings = check_hints(text) + check_emphasis(text) + check_numbers(slug, text)
    if not findings:
        print("   none")
        return 0
    for f in findings:
        print("   %s" % f)
    return 1


if __name__ == "__main__":
    sys.exit(main())
