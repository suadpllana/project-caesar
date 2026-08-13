"""Structural screen for instruction briefs.

textcheck.py measures cadence and register. It passed every version of
typeahead-query-controller that the AI screen then rejected, three times, so the
axes it measures are demonstrably not the ones that decide the outcome.

This checks the properties that actually separated the rejected drafts from the
briefs that cleared the screen. Every threshold below was validated in both
directions: clean on rollout-cache-coherence, checkpoint-resume-drift and
reaction-network-reconstruction, and firing on the rejected typeahead drafts.

Run it as:  python tools/structcheck.py <draft.md> [<draft2.md> ...]
"""
import re
import sys

# Inline category labels: a Title-case NOUN PHRASE with no verb, terminated by a
# period, opening a paragraph. This is a bulleted spec with the bullets deleted, and
# it is the shape the second typeahead rejection carried.
#
# Validated against false positives: short verdict sentences ("None of them care.",
# "Answer it.", "Ours is neither.") are real sentences with a verb and must not fire,
# which is why the label must contain no verb and must start its paragraph. Only
# paragraph-initial labels count - a verdict mid-paragraph is prose, not a bucket.
VERBS = r"\b(is|are|was|were|has|have|had|does|do|did|must|will|can|goes|gets|" \
        r"care|answer|work|comes|come|run|runs|give|gives|throw|holds|hold|need|" \
        r"belongs|stays|means|reads|lands|fires|keeps|paints)\b"
LABEL = re.compile(r"^[A-Z][a-z]+(?:\s+(?:and|or)?\s*[a-z]+){0,3}\.\s")

# Documentation furniture. None of the three passing briefs contains an indented
# code sample or an aligned // comment column; the rejected drafts all did.
CODEISH = re.compile(r"^(\s{4,}\S|```)")
ALIGNED_COMMENT = re.compile(r"\S\s{2,}//")

# A grounded brief quotes real output: bare integers, quoted string lists, or
# identifier-shaped literals from an actual run.
NUMERIC = re.compile(r"\b\d{2,}\b")


def paragraphs(text: str) -> list:
    return [p for p in text.split("\n\n") if p.strip()]


def strip_suffix(text: str) -> str:
    lines = text.rstrip().split("\n")
    while lines and not lines[-1].strip():
        lines.pop()
    if lines and "Do not cheat by using online solutions" in lines[-1]:
        lines.pop()
    return "\n".join(lines)


def analyse(path: str) -> dict:
    raw = open(path, encoding="utf-8").read()
    body = strip_suffix(raw)
    lines = body.split("\n")
    paras = paragraphs(body)

    # Only paragraph-initial, verb-free noun phrases count as buckets.
    labels = []
    for p in paras:
        first = p.strip().split("\n")[0]
        m = LABEL.match(first)
        if m and not re.search(VERBS, m.group(0), re.I):
            labels.append(first)

    code = [l for l in lines if CODEISH.match(l)]
    aligned = [l for l in lines if ALIGNED_COMMENT.search(l)]

    # Grounding: numbers in the first third, where the passing briefs put the
    # observed run. A brief that only cites numbers inside its spec is asserting,
    # not demonstrating. Data-analysis tasks (reaction-network) legitimately have
    # no numeric run to quote and instead enumerate concrete artifacts, so a
    # /app path inventory counts as grounding too.
    head = "\n".join(paras[:max(1, len(paras) // 3)])
    return {
        "path": path,
        "words": len(body.split()),
        "paras": len(paras),
        "labels": labels,
        "code": code,
        "aligned": aligned,
        "leading_blank": raw.startswith("\n"),
        "head_numbers": len(NUMERIC.findall(head)),
        "head_paths": len(re.findall(r"/app\S*", head)),
        "nonascii": sorted({c for c in body if ord(c) > 127}),
        "crlf": "\r\n" in raw,
    }


def report(a: dict) -> int:
    print("== %s" % a["path"])
    print("   words %d  paragraphs %d  numbers in opening third %d"
          % (a["words"], a["paras"], a["head_numbers"]))
    findings = []

    if a["labels"]:
        findings.append("labeled requirement buckets (%d): %s - the passing briefs use one "
                        "pivot line then unlabeled prose"
                        % (len(a["labels"]), "; ".join(x.strip()[:40] for x in a["labels"][:4])))
    if a["code"]:
        findings.append("%d indented/fenced code lines - none of the three passing briefs "
                        "carries a code block" % len(a["code"]))
    if a["aligned"]:
        findings.append("%d aligned // comment columns - generated-documentation furniture"
                        % len(a["aligned"]))
    # reaction-network grounds on a data inventory rather than a numeric run and sits
    # at 2 /app references; the rejected typeahead drafts sat at 1 number + 2 paths but
    # failed the code-block and label rules instead. Threshold set at what the passing
    # set actually supports, not at a rounder number.
    if a["head_numbers"] < 3 and a["head_paths"] < 2:
        findings.append("opening third has %d multi-digit numbers and %d /app references: the "
                        "bug is asserted rather than demonstrated from a real run"
                        % (a["head_numbers"], a["head_paths"]))
    if a["leading_blank"]:
        findings.append("file starts with a blank line; the passing briefs do not")
    if a["nonascii"]:
        findings.append("non-ascii characters present: %r" % a["nonascii"])
    if a["crlf"]:
        findings.append("CRLF line endings")

    if findings:
        for f in findings:
            print("   FIX  %s" % f)
    else:
        print("   none")
    return len(findings)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(2)
    bad = 0
    for p in sys.argv[1:]:
        bad += report(analyse(p))
        print()
    raise SystemExit(1 if bad else 0)
