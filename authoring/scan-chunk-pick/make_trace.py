"""Write authoring/scan-chunk-pick/trace.md from the verifier, with every quote checked.

Each quote is asserted to be in instruction.md before the table is written, so a trace cannot
go stale behind an edit to the brief without this failing first.
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "scan-chunk-pick"
BRIEF = (TASK / "instruction.md").read_text(encoding="utf-8")

Q = {
 "seg": "opens the file with the statistics granularity, the row count and the column count",
 "ch": "is one chunk of column C over n rows, u of them null, with mn and mx the recorded low and high over the rest",
 "part": "The partitions of two columns need not line up.",
 "plain": "A `p` chunk lists its n values, `-` for a null",
 "dict": "then one token per row: an index into the dictionary, `-` for a null, or `*` and a value the dictionary does not hold",
 "query": "`qry` opens a query, `prd` carries one condition, `prj` names the columns to report and `end` closes it",
 "kinds": "A condition is `ge C v`, `le C v`, `eq C v` or `ne C v` against a value, or `nn C` and `nu C` for not-null and null",
 "nullsat": "A null satisfies `nu` and nothing else.",
 "example": "The seven lines it should print are `qry 0`, `rd 0 0`, `dc 0 0`, `sel 4 2000021000077000102`, `dc 1 0`, `prj 1 4 16` and `prj 0 4 30`",
 "files": "The files you may change are `/app/scn/hdr.py`, `/app/scn/dct.py`, `/app/scn/live.py`, `/app/scn/pick.py`, `/app/scn/step.py` and `/app/scn/proj.py`. Nothing else.",
 "replaced": "The rest of the tree is replaced by our own copy before a segment file is run, a new file put beside those six included.",
 "entry": "calls `live.start`, `pick.run`, `live.rows` and `proj.run` in that order, so those four keep their names and the arguments they are handed",
 "exact": "Under `e` the recorded pair is the pair to use.",
 "widen": "Under `w` it was rounded inward to a multiple of G, so the low to use is the recorded low less G-1 and the high is the recorded high plus G-1.",
 "allnull": "A chunk whose nulls are all its rows writes both as `-` and has no bounds.",
 "liverows": "Call those its live rows.",
 "tmiss": "What proves the first is the high below v for `ge v`, the low above v for `le v`, v outside the bounds for `eq v`, a low and a high that are both v for `ne v`, no live rows at all for `nn`, and no nulls at all for `nu`",
 "tall": "what proves the second is the low at least v for `ge v`, the high at most v for `le v`, a low and a high that are both v again for `eq v`, v outside the bounds again for `ne v`, no nulls for `nn`, and every row null for `nu`",
 "tests": "A chunk is dropped unread when the header proves no row of it satisfies the condition, and kept unread when the header proves every row does.",
 "nullblock": "Apart from `nu`, a chunk holding any null is never kept unread, and a chunk with no live rows is dropped unread under a comparison as it is under `nn`.",
 "spread": "For that a condition has a count on a chunk: the live rows spread evenly over the bounds.",
 "parts": "the high less v plus one for `ge v`, v less the low plus one for `le v`, and one for `eq v` and `ne v` when v lies within the bounds and none when it does not",
 "empty": "Where it comes out at nothing or less the count is zero for `ge v`, `le v` and `eq v`, and every live row for `ne v`.",
 "round": "cut the part down to the width of the bounds, multiply the live rows by it, divide by that width and round up",
 "spne": "for `ne v` it is the live rows less it",
 "spnn": "`nn` counts the live rows and `nu` counts the nulls, and a chunk with no live rows counts nothing for anything but `nu`.",
 "dwhole": "A `d` chunk none of whose tokens is a value written with `*` can answer a comparison from its dictionary alone.",
 "dfirst": "A chunk the header has settled never reaches its dictionary.",
 "dcharge": "That dictionary is charged once. The first condition to reach it prints `rd` with the column and the chunk number, and a later one on the same chunk prints nothing.",
 "dverdict": "No entry satisfying the condition drops the chunk; every entry satisfying it with the chunk holding no nulls keeps it; anything else reads the chunk.",
 "dnonull": "`nn` and `nu` are never answered from a dictionary. Nor is a chunk that has already been read.",
 "rprint": "Reading a chunk prints `dc`, the column and the chunk number.",
 "rsettle": "It settles the exact count of every condition of the query over that column, counted over all of the rows of the chunk rather than over the rows still alive, and that count stands in for the spread on that chunk from then on.",
 "rfilter": "The condition being applied then drops the surviving rows of the chunk that do not satisfy it.",
 "pending": "A condition and a chunk of its column are a pending pair while the condition has not been applied to that chunk and the chunk still holds a surviving row.",
 "choice": "The pair taken next is the one expected to leave the fewest rows alive, which is the smaller of the rows that chunk still holds and the count of the condition on it.",
 "tie": "A tie goes to the condition written earlier in the query. Then to the lower chunk number.",
 "done": "The conditions are done when nothing is pending.",
 "sel": "Then comes `sel`, the number of surviving rows and a digest of them: start at zero and, for each surviving row in ascending order, multiply by 1000003, add the row number plus one and take the remainder by 2305843009213693951.",
 "prjorder": "After it every column the query names is reported, in the order it names them and once for each time it names it.",
 "prjread": "A chunk of that column that still holds a surviving row and has not been read is read before the line for its column.",
 "prjline": "That line is `prj`, the column, the count of surviving rows whose value there is not null, and the sum of those values.",
 "qryline": "`qry` and the number of the query, counted from 0 within the file, opens each query, and nothing else is printed.",
 "reset": "Every query starts over: every row alive, nothing read, no dictionary charged.",
 "wide": "`/app/segs/wide.txt` is forty thousand rows over five columns in chunks of about two hundred.",
 "deep": "`/app/segs/deep.txt` is forty thousand rows over four columns in chunks of about two thousand, with seven conditions to a query.",
 "limit": "The graded set is three segment files of each of those two shapes, three hundred smaller ones and thirty-one written by hand, and all of it has to get through inside 60 seconds.",
}

for key, text in Q.items():
    assert '"' not in text, key
    assert len(text.split()) >= 4, key
    if text not in BRIEF:
        raise SystemExit("quote %r is not in instruction.md: %s" % (key, text[:70]))


def q(*keys):
    return " ".join('"%s"' % Q[k] for k in keys)


GRADED = [
 ("`tests/test_outputs.py:117` test_the_model_still_reproduces_the_frozen_answers",
  "the sealed model still reproduces the frozen answers; grades nothing by itself",
  q("example")),
 ("`tests/test_outputs.py:127` test_hand_case",
  "every line of every hand-written segment file, in order, against the frozen answers",
  q("qryline", "example")),
 ("`tests/test_outputs.py:136` test_every_drawn_segment_matches",
  "every line of every generated segment file, in order, against the sealed model",
  q("limit")),
 ("`tests/test_outputs.py:155` test_every_family_is_represented",
  "that the generated population covers all twelve families",
  q("limit")),
 ("artifact `/app/scn/hdr.py`", "only the declared files are collected", q("files", "replaced")),
 ("artifact `/app/scn/dct.py`", "only the declared files are collected", q("files", "replaced")),
 ("artifact `/app/scn/live.py`", "only the declared files are collected", q("files", "replaced")),
 ("artifact `/app/scn/pick.py`", "only the declared files are collected", q("files", "replaced")),
 ("artifact `/app/scn/step.py`", "only the declared files are collected", q("files", "replaced")),
 ("artifact `/app/scn/proj.py`", "only the declared files are collected", q("files", "replaced")),
 ("`tests/test.sh:37` a 60 s clock", "the whole graded set inside one wall clock", q("limit", "wide", "deep")),
 ("`tests/worker.py:45` the collected files laid over a pristine tree",
  "a seventh file beside the six is never collected, and the driver's entry points are fixed",
  q("replaced", "entry")),
 ("`tests/seal/model.py:42-97` _read", "the segment grammar: header, chunk lines, queries",
  q("seg", "ch", "plain", "dict", "query")),
 ("`tests/seal/model.py:42-97` _read", "a column's chunks cover every row and two columns need not agree",
  q("part")),
 ("`tests/seal/model.py:99-105` _span", "an exact recorded pair is used as written", q("exact")),
 ("`tests/seal/model.py:99-105` _span", "a widened pair is pushed out by the granularity less one", q("widen")),
 ("`tests/seal/model.py:99-105` _span", "an all-null chunk has no bounds", q("allnull")),
 ("`tests/seal/model.py:107-121` _holds", "what each condition means on one value", q("kinds", "nullsat")),
 ("`tests/seal/model.py:124-143` _none", "the header proves no row matches, per condition kind",
  q("tests", "tmiss", "liverows")),
 ("`tests/seal/model.py:145-162` _all", "the header proves every row matches, per condition kind",
  q("tests", "tall")),
 ("`tests/seal/model.py:145-162` _all", "a chunk holding a null is never kept unread, is-null apart",
  q("nullblock")),
 ("`tests/seal/model.py:165-188` _spread", "the interpolation: the width of the part per condition kind",
  q("spread", "parts")),
 ("`tests/seal/model.py:165-188` _spread", "an empty part counts nothing, or every live row for ne",
  q("empty")),
 ("`tests/seal/model.py:165-188` _spread", "the share is rounded up, and ne takes the complement",
  q("round", "spne")),
 ("`tests/seal/model.py:165-188` _spread", "not-null counts the live rows and is-null the nulls",
  q("spnn")),
 ("`tests/seal/model.py:191-217` _one", "a query starts with every row alive and nothing read",
  q("reset")),
 ("`tests/seal/model.py:218-224` strike", "a row that dies leaves one chunk of every column",
  q("part", "pending")),
 ("`tests/seal/model.py:243-260` the choice loop", "a pending pair, and the pair taken next",
  q("pending", "choice")),
 ("`tests/seal/model.py:243-260` the choice loop", "the two tie-breaks", q("tie")),
 ("`tests/seal/model.py:243-260` the choice loop", "a read chunk is scored by its exact count",
  q("rsettle")),
 ("`tests/seal/model.py:243-260` the choice loop", "the conditions end when nothing is pending",
  q("done")),
 ("`tests/seal/model.py:263-267` the header decisions", "dropped unread, then kept unread",
  q("tests")),
 ("`tests/seal/model.py:268-280` the dictionary", "only a chunk with no literal token answers from its dictionary",
  q("dwhole")),
 ("`tests/seal/model.py:263-267` the header decisions", "the header is asked before the dictionary",
  q("dfirst")),
 ("`tests/seal/model.py:268-280` the dictionary", "the charge is once per chunk", q("dcharge")),
 ("`tests/seal/model.py:268-280` the dictionary", "the three verdicts", q("dverdict")),
 ("`tests/seal/model.py:268-280` the dictionary", "never for a null test, never for a read chunk",
  q("dnonull")),
 ("`tests/seal/model.py:228-237` fetch", "a read prints dc and settles every condition of the column",
  q("rprint", "rsettle")),
 ("`tests/seal/model.py:238-242` apply", "the condition then drops the survivors that fail it",
  q("rfilter")),
 ("`tests/seal/model.py:283-287` the digest", "the count and the digest of the surviving rows", q("sel")),
 ("`tests/seal/model.py:289-304` the report pass", "the columns in the order the query names them",
  q("prjorder")),
 ("`tests/seal/model.py:289-304` the report pass", "only a chunk holding a survivor and not read already",
  q("prjread")),
 ("`tests/seal/model.py:289-304` the report pass", "the two figures on the line", q("prjline")),
 ("`tests/seal/model.py:306-312` expect", "the query line and its number, and nothing else printed",
  q("qryline")),
]

CASE_ROWS = {
 "hdr-widen-high": ("a widened high bound reaches above the value", q("widen", "tmiss")),
 "hdr-widen-low": ("a widened low bound reaches below the value", q("widen", "tmiss")),
 "hdr-widen-eq": ("a widened pair is not a single value", q("widen", "tall")),
 "hdr-widen-ne": ("a widened pair does not rule a value out", q("widen", "tmiss")),
 "hdr-miss-skip": ("a chunk the header rules out is dropped unread", q("tests", "tmiss", "tall")),
 "hdr-all-pass": ("a chunk the header proves whole is kept unread", q("tests", "tmiss", "tall")),
 "hdr-nulls-block-pass": ("a chunk holding nulls is never kept unread", q("nullblock")),
 "hdr-ne-exact-miss": ("a one-value chunk under ne is dropped unread", q("tmiss")),
 "hdr-null-chunk-null": ("an all-null chunk under is-null and under is-not-null", q("tmiss", "tall")),
 "hdr-nu-no-nulls": ("a chunk with no nulls under is-null", q("tmiss", "prjline")),
 "dic-whole-drop": ("no dictionary entry matching drops the chunk", q("dverdict")),
 "dic-whole-keep": ("every entry matching with no nulls keeps it", q("dverdict")),
 "dic-whole-read": ("some entries matching reads it", q("dverdict")),
 "dic-overflow-read": ("a dictionary with a literal token answers nothing", q("dwhole")),
 "dic-charge-once": ("a second condition on the same chunk prints no read", q("dcharge")),
 "dic-nulls-read": ("every entry matching but the chunk holds nulls", q("dverdict")),
 "dic-not-for-null": ("is-not-null is never answered from a dictionary", q("dnonull")),
 "dic-drop-with-nulls": ("a ruled-out chunk is dropped although it holds nulls",
                         q("dverdict", "nullsat")),
 "prj-dead-chunk": ("a reported chunk with no survivor is not read", q("prjread")),
 "prj-listed-order": ("the columns in the order the query names them", q("prjorder")),
 "prj-same-twice": ("a column named twice is reported twice", q("prjorder")),
 "prj-nulls-out": ("nulls are out of both reported figures", q("prjline")),
 "prj-reuse-read": ("a chunk read by a condition is not read again", q("prjread")),
 "ord-nothing-prunes": ("nothing prunes and only the interleaving differs",
                        q("pending", "choice", "tie")),
 "ord-keeps-all": ("every condition keeps everything and nothing is dropped", q("tests", "tmiss", "tall")),
 "ord-spread-rounds-up": ("the share is rounded up", q("round")),
 "ord-spread-takes-edge": ("the part includes its endpoint", q("parts")),
 "ord-exact-after-read": ("a read chunk is scored by its exact count afterwards",
                          q("rsettle", "choice")),
 "dec-hits-whole-chunk": ("the exact count is over all the chunk's rows", q("rsettle")),
 "qry-starts-over": ("the second query reads what the first already read", q("reset")),
 "sel-empty": ("nothing survives, and the report reads nothing", q("sel", "prjread")),
}

READINGS = {
 "hdr-bounds-exact": (q("widen"), "hdr-widen-eq"),
 "hdr-pass-ignores-nulls": (q("nullblock"), "hdr-nulls-block-pass"),
 "hdr-null-always-read": (q("tmiss", "tall"), "hdr-nu-no-nulls"),
 "hdr-spread-floor": (q("round"), "ord-spread-rounds-up"),
 "hdr-spread-open": (q("parts"), "ord-spread-takes-edge"),
 "dic-overflow-used": (q("dwhole"), "dic-overflow-read"),
 "dic-charge-each": (q("dcharge"), "dic-charge-once"),
 "dic-keep-ignores-nulls": (q("dverdict"), "dic-nulls-read"),
 "dic-answers-null": (q("dnonull"), "dic-not-for-null"),
 "dic-drop-needs-nulls": (q("dverdict", "nullsat"), "dic-drop-with-nulls"),
 "ord-fixed-sweep": (q("pending", "choice"), "ord-nothing-prunes"),
 "ord-column-sum": (q("choice"), "ord-nothing-prunes"),
 "ord-no-cap": (q("choice"), "ord-nothing-prunes"),
 "ord-header-only": (q("rsettle"), "ord-exact-after-read"),
 "ord-highest-chunk": (q("tie"), "ord-nothing-prunes"),
 "ord-largest-first": (q("choice"), "ord-nothing-prunes"),
 "dec-one-cond": (q("rsettle"), "ord-exact-after-read"),
 "dec-hits-live-only": (q("rsettle"), "dec-hits-whole-chunk"),
 "prj-all-chunks": (q("prjread"), "dic-drop-with-nulls"),
 "prj-index-order": (q("prjorder"), "prj-listed-order"),
 "prj-nulls-counted": (q("prjline"), "hdr-nu-no-nulls"),
 "prj-redecode": (q("prjread"), "hdr-nu-no-nulls"),
 "qry-keeps-state": (q("reset"), "dic-drop-with-nulls"),
}

SHORTCUTS = [
 ("the shipped tree unchanged (the nop)",
  "reward 0 in the two-container trial; 19 of 34 grader tests failed"),
 ("a constant: one fixed two-line output for every segment file (`cheat-const-nothing`)",
  "reward 0; matches 0 of 337 graded files"),
 ("positional: the conditions in query order over whole columns (`cheat-pos-query-order`)",
  "reward 0; matches 0 of 337 graded files"),
 ("the worked example's output replayed for every file (`cheat-replay-example`)",
  "reward 0; matches 1 of 337 graded files, and that one only because tiny.txt is not graded"),
 ("the frozen answers for the enumerated set carried in a collected file (`cheat-forge-hand`)",
  "reward 0; matches all 31 hand files and 0 of the 306 it could not have seen"),
]

TOLERANCES = [
 ("`tests/test.sh:37` the 60 second clock on the graded run",
  "`authoring/scan-chunk-pick/variants/ok-slice` (no maintained counts, a byte slice summed) "
  "and `authoring/scan-chunk-pick/variants/ok-bisect` (counts in a dict, the owning chunk found "
  "by binary search), both written apart from the reference",
  "whole graded set: reference 1.81 s, ok-bisect 2.13 s, ok-slice 4.55 s, all against 60 s. "
  "The naive family the limit rules out is the survivors held as a collection of row ids that "
  "every score walks (`cheat-slow-rowid-set`): 398.26 s on `wide.txt` against 0.50 s for the "
  "reference, 9.79 s on `deep.txt` against 0.13 s, with a trace identical to the reference's."),
]


def table(rows, head):
    out = ["| " + " | ".join(head) + " |", "|" + "---|" * len(head)]
    for row in rows:
        out.append("| " + " | ".join(row) + " |")
    return "\n".join(out)


def main():
    sys.path.insert(0, str(TASK / "tests"))
    import cases
    missing = [n for n in cases.ORDER if n not in CASE_ROWS]
    if missing:
        raise SystemExit("no trace row for enumerated cases: %s" % missing)

    lines = (TASK / "tests" / "cases.py").read_text(encoding="utf-8").split("\n")
    at = {}
    for i, ln in enumerate(lines):
        if ln.startswith('_add("'):
            at[ln.split('"')[1]] = i + 1

    graded = list(GRADED)
    for name in cases.ORDER:
        what, sentence = CASE_ROWS[name]
        graded.append(("`tests/cases.py:%d` case %s" % (at[name], name), what, sentence))

    body = [
        "# Instruction trace: scan-chunk-pick",
        "",
        "Walked from the verifier toward the instruction (docs/INSTRUCTION-CONTRACT.md). Every",
        "quote is checked against `instruction.md` by `authoring/scan-chunk-pick/make_trace.py`",
        "before this file is written, so a stale quote cannot survive an edit to the brief.",
        "Check with `python tools/tracecheck.py scan-chunk-pick`.",
        "",
        "## Graded assertions",
        "",
        table([(a, b, c) for a, b, c in graded],
              ["Verifier site", "What it grades", "Instruction sentence"]),
        "",
        "## Readings",
        "",
        table([(k, v[0], v[1]) for k, v in READINGS.items()],
              ["Reading", "Sentence or published example that rules it out", "Case that separates it"]),
        "",
        "## Shortcuts",
        "",
        table(SHORTCUTS, ["Strategy", "Result"]),
        "",
        "## Tolerances",
        "",
        table(TOLERANCES, ["Tolerance or limit", "Independent implementation", "Measured"]),
        "",
    ]
    text = "\n".join(body)
    assert "\r" not in text
    with open(HERE / "trace.md", "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    print("wrote trace.md: %d graded rows, %d readings" % (len(graded), len(READINGS)))


if __name__ == "__main__":
    main()
