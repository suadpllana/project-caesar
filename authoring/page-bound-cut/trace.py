"""Write trace.md: every graded assertion against the sentence that tells the agent about it.

Generated rather than typed, so a quote that has fallen out of the instruction is caught here
rather than by tracecheck: every quote below is asserted to appear in instruction.md verbatim
before the file is written.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

BRIEF = (lab.TASK / "instruction.md").read_text(encoding="utf-8")

Q = {
    "collect": "Only `/app/pg/fit.py`, `/app/pg/bound.py`, `/app/pg/cut.py`, `/app/pg/join.py` and",
    "entry": "must keep the entry point `one(tr, kind, key, out)`",
    "fmt": "first non-blank line is `page <capacity> <floor>`, both counts of bytes",
    "keys": "A key is 1 to 10 lowercase letters",
    "bounds": "a capacity between 32 and 160 and a floor between 10 and one less than the capacity",
    "start": "The index starts as a single empty leaf page",
    "size": "Its stored size is 8 bytes, plus 2 bytes for every child it points at",
    "prefix": "the longest common prefix of its entries once and then 2 bytes and the remaining characters",
    "cap": "over capacity when that size is greater than the declared capacity",
    "floor": "under the floor when it is less than the declared floor",
    "sep": "the shortest string that is greater than the greatest key in the subtree on its left",
    "inv": "Every string in the index is that string once an operation has finished",
    "quiet": "printed only when its value actually changes",
    "order": "put right before any page is measured against the capacity or the floor",
    "walk": "the pages from the leaf up to the root are visited once each",
    "prec": "A page that holds nothing leaves the index; otherwise a page over capacity is cut",
    "cand": "Every position that leaves at least one entry on each side is considered",
    "leafcut": "cutting at position `i` leaves keys 0 to `i-1` behind and moves the rest to a new page",
    "twigcut": "promotes the string at `i` itself, which leaves this page",
    "cost": "costs the larger of the two resulting pages plus what the promoted string adds",
    "rootcost": "that second part is the whole stored size of the new root",
    "tie": "the lowest such position when several cost the same",
    "cutids": "The cut page keeps its id and the other half is a fresh page",
    "rootorder": "that fresh page is taken before the fresh root",
    "recut": "still over capacity once it has been cut is left as it is",
    "joinright": "the one on its right when the joined page would be within capacity",
    "joinleft": "otherwise the one on its left on the same test, otherwise neither",
    "joinsurv": "The right page's entries move into the left one, which keeps its id",
    "joinmid": "the string that divided them comes down into the survivor",
    "rootjoin": "The root is never joined",
    "empty": "leaves the index, and the page above drops it along with one of the two strings beside it",
    "emptyside": "the one on its left when it has a left neighbour, otherwise the one on its right",
    "rootleaf": "There is one exception. An empty root leaf stays",
    "cascade": "only the last removal of such a run puts a string right",
    "fold": "While the root is an internal page with a single child, that child becomes the root",
    "ids": "given the smallest positive whole number that no page is using",
    "reuse": "a freed id can be given out again",
    "events": "prints its events in the order the work is done, a line each",
    "add": "names the leaf a key went into",
    "dup": "a put found the key already there or a delete did not find it at all",
    "rm": "`rm <key> p<id>` the leaf it came out of",
    "none": "a delete did not find it at all, and in those two cases nothing else happens",
    "boundline": "the internal page holding a string that changed, its position there counting from 0",
    "cutline": "the fresh page beside it, the position it was cut at, and the string that went up",
    "goneline": "A page leaving the index prints `gone p<id>`",
    "joinline": "gives the survivor first and the freed page second",
    "rootline": "A fresh root over a cut root prints `root p<id>`",
    "foldline": "A root replaced by its single child prints `fold p<id>`, naming that child",
    "compare": "Every graded program is compared line for line",
    "clock": "the whole graded set has to finish within 120 seconds",
    "scale": "about 93000 operations and about 60000 operations, both at a capacity of 96",
}

for key, text in Q.items():
    if text not in BRIEF:
        raise SystemExit("trace: quote %r is not in instruction.md:\n  %s" % (key, text))
    if '"' in text:
        raise SystemExit("trace: quote %r carries a double quote" % key)


def q(*keys):
    return " ".join('"%s"' % Q[k] for k in keys)


TESTS = [
    ("`tests/test_outputs.py:120` test_the_model_still_reproduces_the_frozen_answers",
     "the sealed model has to agree with the frozen answers before it judges anything; it "
     "grades no behaviour of its own", q("compare")),
    ("`tests/test_outputs.py:131` test_enumerated_program",
     "the whole printed trace of each enumerated program, line for line, against answers "
     "frozen before the grading file existed", q("compare", "events")),
    ("`tests/test_outputs.py:141` test_every_generated_program",
     "the whole printed trace of every generated program against the sealed model",
     q("compare")),
    ("`tests/test_outputs.py:160` test_every_family_is_represented",
     "that the generated population still covers every family, so a shrunken run cannot pass",
     q("compare")),
]

CASES = {
    "bound-late": ("a string put right after the pages were measured instead of before", ("order",)),
    "bound-lowonly": ("a lost greatest key moves a string as surely as a lost least key", ("inv",)),
    "bound-never": ("a string worked out again at all", ("inv",)),
    "bound-parent": ("the string to put right sits above the parent", ("inv", "sep")),
    "cap-loose": ("a page exactly at the capacity is not over it", ("cap",)),
    "cut-mid": ("the cut position is the scored one and not the middle entry", ("cost", "cand")),
    "cut-nopar": ("the score includes what the promoted string costs the page above", ("cost",)),
    "cut-sum": ("the score is the larger of the halves, not the two added", ("cost",)),
    "cut-tiehigh": ("a tie in the score goes to the lower position", ("tie",)),
    "fit-ordinary": ("a page within capacity once its prefix is credited is not cut at all",
                     ("prefix", "cap")),
    "fit-tips": ("the same keys taken past the capacity are cut once", ("cap", "cand")),
    "floor-loose": ("a page exactly at the floor is not under it", ("floor",)),
    "fold-once": ("the root folds again while it still has a single child", ("fold",)),
    "gone-cascade": ("only the last removal of a run puts a string right", ("cascade",)),
    "gone-quiet": ("a removal does put the surviving string right", ("empty", "cascade")),
    "gone-right": ("the string on the left goes when there is a left neighbour", ("emptyside",)),
    "id-reuse": ("a freed page id is handed out again", ("ids", "reuse")),
    "join-flat": ("the joined page is measured over the union, not as two sizes added",
                  ("joinright", "prefix")),
    "join-left": ("the neighbour on the right is tried first", ("joinright", "joinleft")),
    "join-nomid": ("an internal join brings the dividing string down", ("joinmid",)),
    "join-stuck": ("a page under the floor with no neighbour that fits stays as it is",
                   ("joinleft",)),
    "root-drains": ("an emptied root leaf stays and takes keys again", ("rootleaf",)),
    "root-order": ("the fresh half is taken before the fresh root", ("rootorder", "cutids")),
    "sep-far": ("a dividing string one character long where the key is nine", ("sep",)),
    "sep-left": ("the string is truncated out of the right key", ("sep",)),
    "sep-nested": ("the left key being a prefix of the right one", ("sep",)),
    "sep-short": ("the string runs one character past where the two keys part", ("sep",)),
    "sep-whole": ("the string is the shortest one, not the whole key", ("sep",)),
    "size-flat": ("the common prefix is credited once and taken off every entry", ("prefix",)),
    "tower": ("a cut of an internal page and a fresh root over it", ("twigcut", "rootcost")),
    "twice-missing": ("a put of a key already there and a delete of one that is not",
                      ("dup", "none")),
}

MODEL = [
    ("`tests/seal/model.py:25-50` parse", "the program format, the header line and the key shape",
     q("fmt", "keys")),
    ("`tests/seal/model.py:52-66` common", "the common prefix of a page's entries", q("prefix")),
    ("`tests/seal/model.py:68-75` divider", "the dividing string between two keys", q("sep")),
    ("`tests/seal/model.py:77-86` measure", "the stored size of a page", q("size", "prefix")),
    ("`tests/seal/model.py:99-107` Idx.__init__", "the index starts as one empty leaf",
     q("start")),
    ("`tests/seal/model.py:108-121` make, toss", "page ids and their reuse", q("ids", "reuse")),
    ("`tests/seal/model.py:126-131` size, where", "a page measured over its own entry list",
     q("size")),
    ("`tests/seal/model.py:133-149` find, low_end, high_end",
     "the keys a dividing string is worked out from", q("sep")),
    ("`tests/seal/model.py:151-168` before, after",
     "which string a changed least or greatest key belongs to", q("inv", "sep")),
    ("`tests/seal/model.py:170-185` mend",
     "a string worked out again, and printed only when it changes", q("inv", "quiet")),
    ("`tests/seal/model.py:187-194` above_cost",
     "what a promoted string adds to the page above, or the cost of a fresh root",
     q("cost", "rootcost")),
    ("`tests/seal/model.py:196-217` plan",
     "the candidate positions, the score and the tie", q("cand", "cost", "tie")),
    ("`tests/seal/model.py:219-254` cut",
     "the halves, the promoted string, the fresh page and the fresh root, in that order",
     q("leafcut", "twigcut", "cutids", "rootorder")),
    ("`tests/seal/model.py:256-275` pair_size, fuse",
     "the joined page measured over the union, the survivor, and the string brought down",
     q("joinright", "joinsurv", "joinmid")),
    ("`tests/seal/model.py:277-288` knit", "right neighbour first, then left, then not at all",
     q("joinright", "joinleft")),
    ("`tests/seal/model.py:290-309` strip",
     "a page that holds nothing leaves, which string goes with it, and the run that follows",
     q("empty", "emptyside", "cascade")),
    ("`tests/seal/model.py:311-322` fold", "the root replaced by its single child", q("fold")),
    ("`tests/seal/model.py:324-342` put",
     "the key goes in, the string is put right, then the pages are visited upward",
     q("add", "dup", "order", "walk")),
    ("`tests/seal/model.py:344-368` drop",
     "the key comes out, the string is put right, then removal, join and fold upward",
     q("rm", "none", "order", "walk", "prec", "rootjoin")),
    ("`tests/seal/model.py:370-377` trace", "one line per event, in the order the work is done",
     q("events")),
]

EVENTS = [
    ("`tests/seal/model.py:330` add line", "the leaf a key went into", q("add")),
    ("`tests/seal/model.py:328` dup line", "a key already present", q("dup")),
    ("`tests/seal/model.py:352` rm line", "the leaf a key came out of", q("rm")),
    ("`tests/seal/model.py:350` none line", "a key that was not there", q("none")),
    ("`tests/seal/model.py:184` bound line", "the page and the position of a changed string",
     q("boundline", "quiet")),
    ("`tests/seal/model.py:236` cut line", "the two pages, the position and the promoted string",
     q("cutline")),
    ("`tests/seal/model.py:307` gone line", "a page that left the index", q("goneline")),
    ("`tests/seal/model.py:274` join line", "the survivor and the page that was freed",
     q("joinline")),
    ("`tests/seal/model.py:245` root line", "a fresh root over a cut root", q("rootline")),
    ("`tests/seal/model.py:321` fold line", "the child that became the root", q("foldline")),
]

READINGS = [
    ("size-flat: a page costs the sum of its entries with no prefix credit", q("prefix"), "size-flat"),
    ("cap-loose: over capacity read as at or above the capacity", q("cap"), "cap-loose"),
    ("floor-loose: under the floor read as at or below the floor", q("floor"), "floor-loose"),
    ("sep-whole: the dividing string is the whole first key on the right", q("sep"), "sep-whole"),
    ("sep-short: the string stops at the common prefix, one character short", q("sep"), "sep-short"),
    ("sep-left: the string is truncated out of the left key", q("sep"), "sep-left"),
    ("bound-never: a string is fixed when a page is cut and never revisited", q("inv"), "bound-late"),
    ("bound-parent: only a string held by the parent is put right", q("inv", "sep"), "bound-parent"),
    ("bound-late: the string is put right after the pages are measured", q("order"), "bound-late"),
    ("bound-lowonly: only a lost least key moves a string", q("inv"), "bound-lowonly"),
    ("cut-mid: the cut goes at the middle entry", q("cost"), "bound-parent"),
    ("cut-nopar: the score ignores the page above", q("cost"), "cut-nopar"),
    ("cut-sum: the score adds the two halves instead of taking the larger", q("cost"), "bound-lowonly"),
    ("cut-tiehigh: a tie goes to the higher position", q("tie"), "bound-late"),
    ("root-order: the fresh root is taken before the fresh half", q("rootorder"), "bound-late"),
    ("join-left: the left neighbour is tried first", q("joinright", "joinleft"), "join-left"),
    ("join-flat: the joined page is the two sizes added", q("joinright", "prefix"), "bound-late"),
    ("join-nomid: an internal join drops the dividing string", q("joinmid"), "id-reuse"),
    ("gone-right: the string on the right goes when there is one on the left", q("emptyside"), "gone-cascade"),
    ("gone-quiet: no string is put right after a removal", q("empty", "cascade"), "fold-once"),
    ("gone-cascade: every removal of a run puts a string right", q("cascade"), "gone-cascade"),
    ("fold-once: the root folds at most once in an operation", q("fold"), "fold-once"),
]

SHORTCUTS = [
    ("the shipped tree unchanged (nop)",
     "reward 0, 28 of 34 assertions failing in the container trial"),
    ("constant: never print a structural event (`cheat-const-quiet`)",
     "reward 0; it matches no enumerated program and none of the generated ones"),
    ("positional: always cut at the lowest position (`cheat-pos-low`)", "reward 0"),
    ("positional: always cut at the highest position (`cheat-pos-high`)", "reward 0"),
    ("the enumerated answers replayed from a table (`cheat-forge-hand`)",
     "reward 0; it reproduces all 31 enumerated programs and fails the generated population, "
     "which is what the answers being drawn after the run buys"),
]

LIMITS = [
    ("`tests/test.sh:35` the 120 second clock on the stage that runs submitted code",
     "`authoring/page-bound-cut/variants/ok-list` and `.../ok-worklist`, both written apart "
     "from the reference",
     "ok-list 21.6 s and ok-worklist 1.9 s on the two large programs, against the reference's "
     "1.7 s; the exactly-correct tree-wide sweep in `.../variants/slow-sweep` is over the "
     "limit on the same population. " + q("clock", "scale")),
    ("no numeric tolerance anywhere, the trace is compared string for string",
     "`authoring/page-bound-cut/variants/ok-list`, written apart from the reference, matches "
     "it line for line on 3000 programs",
     "exact equality on every line of every program; " + q("compare")),
]


def main():
    out = ["# Instruction trace: page-bound-cut", "",
           "Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md).",
           "Generated by authoring/page-bound-cut/trace.py, which asserts every quote below is",
           "in instruction.md verbatim before it writes the file.", "",
           "## Graded assertions", "",
           "| Verifier site | What it grades | Instruction sentence |", "|---|---|---|"]
    for site, what, cite in TESTS:
        out.append("| %s | %s | %s |" % (site, what, cite))
    for name in sorted(CASES):
        what, keys = CASES[name]
        line = None
        text = (lab.TASK / "tests" / "cases.py").read_text(encoding="utf-8").splitlines()
        for i, row in enumerate(text, 1):
            if row.strip().startswith("%r:" % name):
                line = i
                break
        out.append("| `tests/cases.py:%d` case %s | %s | %s |" % (line, name, what, q(*keys)))
    for site, what, cite in MODEL + EVENTS:
        out.append("| %s | %s | %s |" % (site, what, cite))
    for art in ("fit.py", "bound.py", "cut.py", "join.py", "step.py"):
        out.append("| artifact `/app/pg/%s` | only the declared files are collected and they are "
                   "laid over a fresh tree | %s |" % (art, q("collect", "entry")))
    out.append("| `tests/test.sh:35` a 120 s clock | the wall clock on the stage that runs "
               "submitted code | %s |" % q("clock", "scale"))
    out += ["", "## Readings", "",
            "| Reading | Sentence or published example that rules it out | Case that separates it |",
            "|---|---|---|"]
    for name, cite, case in READINGS:
        out.append("| %s | %s | `%s` |" % (name, cite, case))
    out += ["", "## Shortcuts", "", "| Strategy | Result |", "|---|---|"]
    for name, got in SHORTCUTS:
        out.append("| %s | %s |" % (name, got))
    out += ["", "## Tolerances", "",
            "| Tolerance or limit | Independent implementation | Measured |", "|---|---|---|"]
    for name, impl, got in LIMITS:
        out.append("| %s | %s | %s |" % (name, impl, got))
    out.append("")
    text = "\n".join(out)
    (HERE / "trace.md").write_text(text, encoding="utf-8", newline="\n")
    print("wrote trace.md: %d rows" % sum(1 for l in out if l.startswith("| `") or l.startswith("| a")))


if __name__ == "__main__":
    main()
