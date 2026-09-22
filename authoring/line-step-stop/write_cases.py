"""Write tests/cases.py: every frozen graded session by name, and what it pins.

Generated from tests/seal/gt.json and readings.py so the names cannot drift; the judge
refuses to grade if the two ever disagree. Run after build_gt.py.
"""
import json
import os

from lab import SEAL, TASK
import readings

OUT = os.path.join(TASK, "tests", "cases.py")

SAMPLE_WHAT = {
    "sample-calls": "shipped sample: ordinary calls, loops and breakpoints; the brief quotes its first six lines",
    "sample-inline": "shipped sample: nested inlined calls, call sites and reveals",
    "sample-rows": "shipped sample: non-statement rows of the next line, split lines, calls in them",
    "sample-long": "shipped sample: loops crossed inside one row, as heavy as the heaviest frozen session",
}


def main():
    doc = json.load(open(os.path.join(SEAL, "gt.json")))
    out = ['"""The frozen graded sessions, by name, and what each one pins.',
           "",
           "The sessions themselves (image, tape, script, expected lines) are sealed in",
           "tests/seal/gt.json; this table is what a reader of the verifier needs to see which",
           "behaviour each one exists to check. judge.py refuses to grade if the names here and in",
           "gt.json ever disagree.",
           '"""', "", "# The four sessions shipped in /app/samples, graded with the rest.", "SAMPLES = {"]
    for s in doc["samples"]:
        out.append("    %r: %r," % (s["name"], SAMPLE_WHAT[s["name"]]))
    out += ["}", "", "# One per wrong reading of the stop rules: under that reading, and only reading it",
            "# the other way, the session prints a different line. Keyed by the reading's name.",
            "CASES = {"]
    for s in doc["cases"]:
        what = readings.EDITS[s["reading"]][0]
        out.append("    %r: %r," % (s["reading"], "separates the reading that " + what))
    out += ["}", "", "# Ordinary sessions - no inlining, no special rows - that an engine which hides,",
            "# reveals or stops more than the rules say prints wrongly.", "FENCES = {"]
    for s in doc["fences"]:
        out.append("    %r: %r," % (s["name"], "ordinary calls and loops, %d commands" % len(s["cmds"])))
    out += ["}", "", "# Loops of up to 700,000 iterations crossed by single commands, in one row, in called",
            "# functions and in inlined instances: what the stated limit is measured on.", "HEAVY = {"]
    for s in doc["heavy"]:
        out.append("    %r: %r," % (s["name"], "%d instructions, %d of them inside a stepping frame" % (
            s["volume"], s["in_frame"])))
    out += ["}", ""]
    text = "\n".join(out)
    assert "\r" not in text
    with open(OUT, "w", newline="\n") as f:
        f.write(text)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
