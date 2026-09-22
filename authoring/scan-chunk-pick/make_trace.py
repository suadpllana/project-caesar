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
 "dict": "then one token per row: an index into the dictionary, `-` for a null, or `*` followed directly by a value the dictionary does not hold",
 "upd": "`up C r v` says row r now holds v in column C, `-` for a null, and `del r` says row r was deleted; each row has at most one update per column.",
 "query": "`qry` opens a query, `prd` carries one condition, `prj` names the columns to report and `end` closes it",
 "kinds": "A condition is `ge C v`, `le C v`, `eq C v` or `ne C v` against a value, or `nn C` and `nu C` for not-null and null",
 "nullsat": "A null satisfies `nu` and nothing else.",
 "example": "The seven lines it should print are `qry 0`, `rd 0 0`, `dc 0 0`, `sel 4 2000021000077000102`, `dc 1 0`, `prj 1 4 16` and `prj 0 4 30`",
 "files": "The files you may change are `/app/scn/hdr.py`, `/app/scn/dct.py`, `/app/scn/live.py`, `/app/scn/pick.py`, `/app/scn/step.py` and `/app/scn/proj.py`. Nothing else.",
 "replaced": "The rest of the tree is replaced by our own copy before a segment file is run, including any new file put beside those six.",
 "entry": "calls `live.start`, `pick.run`, `live.rows` and `proj.run` in that order, so those four keep their names and the arguments they are handed",
 "value": "A row's value in a column is its update when it has one, and what its chunk holds otherwise. A deleted row is never alive.",
 "written": "Everything a chunk says about itself describes the chunk as written: its header, its dictionary and the counts a read of it yields. Deleted rows and replaced values are included.",
 "hfacts": "A header knows two things: u of the chunk's rows are null, and every other value it holds lies between its bounds.",
 "exact": "Under `e` the bounds are the recorded pair.",
 "widen": "Under `w` that pair was rounded inward to a multiple of G, so the bounds are the recorded low less G-1 and the recorded high plus G-1.",
 "allnull": "A chunk whose rows are all null writes both as `-` and has no bounds.",
 "hsettle": "What those two facts prove about every row the chunk holds, the header settles: that a condition fails for all of them, or holds for all of them.",
 "dwhole": "A `d` chunk none of whose tokens is written with `*` holds exactly the values of its entries, each at least once, besides its nulls.",
 "dverdict": "No entry satisfying it fails every row; every entry satisfying it, with the chunk holding no nulls, passes every row. It can never settle `nn` or `nu`. How many entries a dictionary has, and whether any token is written with `*`, is known without consulting it.",
 "dknown": "How many entries a dictionary has, and whether any token is written with `*`, is known without consulting it.",
 "rprint": "Reading a chunk prints `dc`, the column and the chunk number",
 "dcharge": "consulting its dictionary prints `rd` with the same two numbers the first time it happens in a query and nothing after",
 "cheap": "Nothing is consulted or read while something cheaper already answers.",
 "costs": "The header costs nothing, a read already made costs nothing, a dictionary costs its charge, and a read costs a read.",
 "forheld": "A chunk is only ever consulted or read for a live row that takes its value in that column from that chunk.",
 "moved": "When a condition is applied to a chunk, its live rows that carry an update in that column are tested on that value.",
 "steps": "The rest are settled by the header if it can, then by a read already made; otherwise, for a comparison on a chunk whose dictionary has no `*` token, that dictionary is consulted, however little it turns out to settle, before the chunk is read.",
 "die": "Rows the condition fails die.",
 "rsettle": "A read settles the exact count of every condition of the query over that column on that chunk, counted over the chunk as written.",
 "spread": "Before that, the count is the spread of the header.",
 "parts": "the high less v plus one for `ge v`, v less the low plus one for `le v`, and one for `eq v` and `ne v` when v lies within the bounds and none when it does not",
 "empty": "Where it comes out at nothing or less the count is zero for `ge v`, `le v` and `eq v`, and all of the non-null rows of the chunk for `ne v`.",
 "round": "cut the part down to the width of the bounds, multiply the non-null rows by it, divide by that width and round up",
 "spne": "for `ne v` it is the non-null rows less it",
 "spnn": "`nn` counts the non-null rows, `nu` counts the nulls, and a chunk with no bounds counts nothing for anything but `nu`.",
 "pending": "A condition and a chunk of its column are a pending pair while the condition has not been applied to that chunk and the chunk still holds a live row.",
 "choice": "The pair applied next is always the one expected to leave the fewest rows alive. That is the smaller of the live rows that chunk holds and the count of the condition on it.",
 "tie": "A tie goes to the condition written earlier in the query, then to the lower chunk number.",
 "done": "The conditions are done when nothing is pending.",
 "sel": "Then comes `sel`, the number of live rows and a digest of them: start at zero and, for each live row in ascending order, multiply by 1000003, add the row number plus one and take the remainder by 2305843009213693951.",
 "prjorder": "After it every column the query names is reported, in the order it names them and once for each time it names it",
 "prjline": "as `prj`, the column, the count of live rows whose value there is not null, and the sum of those values",
 "prjread": "Before its line, every chunk of that column holding a live row that takes its value from it has its values supplied, in chunk order and on the same terms: by a read already made or by its header when either fixes them, by consulting its dictionary when that fixes them, and by a read otherwise.",
 "qryline": "`qry` and the number of the query, counted from 0 within the file, opens each query, and nothing else is printed.",
 "reset": "Every query starts over: every row not deleted alive, nothing read, no dictionary charged.",
 "wide": "`/app/segs/wide.txt` is sixty thousand rows over five columns in chunks of ten to twenty-four rows, the last in a column sometimes longer, with eight conditions to a query.",
 "deep": "`/app/segs/deep.txt` is forty thousand rows over four columns in chunks of about two thousand, the last in a column sometimes longer, with seven.",
 "graded": "The graded set is three segment files of each of those two shapes, 308 smaller ones and 47 written by hand.",
 "limit": "All of it runs in one Python 3.12 process with nothing but the standard library, and all of it has to get through inside 60 seconds.",
}

for key, text in Q.items():
    assert '"' not in text, key
    assert len(text.split()) >= 4, key
    if text not in BRIEF:
        raise SystemExit("quote %r is not in instruction.md: %s" % (key, text[:70]))


def q(*keys):
    return " ".join('"%s"' % Q[k] for k in keys)


GRADED = [
 ("`tests/test_outputs.py:122` test_the_model_still_reproduces_the_frozen_answers",
  "the sealed model still reproduces the frozen answers; grades nothing by itself",
  q("example")),
 ("`tests/test_outputs.py:132` test_hand_case",
  "every line of every hand-written segment file, in order, against the frozen answers",
  q("qryline", "example", "graded")),
 ("`tests/test_outputs.py:141` test_every_drawn_segment_matches",
  "every line of every generated segment file, in order, against the sealed model",
  q("graded")),
 ("`tests/test_outputs.py:160` test_every_family_is_represented",
  "that the generated population covers all sixteen families",
  q("graded")),
 ("artifact `/app/scn/hdr.py`", "only the declared files are collected", q("files", "replaced")),
 ("artifact `/app/scn/dct.py`", "only the declared files are collected", q("files", "replaced")),
 ("artifact `/app/scn/live.py`", "only the declared files are collected", q("files", "replaced")),
 ("artifact `/app/scn/pick.py`", "only the declared files are collected", q("files", "replaced")),
 ("artifact `/app/scn/step.py`", "only the declared files are collected", q("files", "replaced")),
 ("artifact `/app/scn/proj.py`", "only the declared files are collected", q("files", "replaced")),
 ("`tests/test.sh:38` a 60 s clock", "the whole graded set inside one wall clock, one process, standard library",
  q("limit", "wide", "deep")),
 ("`tests/worker.py:42` the collected files laid over a pristine tree",
  "a seventh file beside the six is never collected, and the driver's entry points are fixed",
  q("replaced", "entry")),
 ("`tests/seal/model.py:47-106` _read", "the segment grammar: header, chunk lines, updates, deletes, queries",
  q("seg", "ch", "plain", "dict", "upd", "query")),
 ("`tests/seal/model.py:47-106` _read", "a column's chunks cover every row and two columns need not agree",
  q("part")),
 ("`tests/seal/model.py:108-114` _span", "an exact recorded pair is used as written", q("exact")),
 ("`tests/seal/model.py:108-114` _span", "a widened pair is pushed out by the granularity less one", q("widen")),
 ("`tests/seal/model.py:108-114` _span", "an all-null chunk has no bounds", q("allnull")),
 ("`tests/seal/model.py:116-131` _holds", "what each condition means on one value", q("kinds", "nullsat")),
 ("`tests/seal/model.py:133-152` _none", "what the header proves: no row the chunk holds matches",
  q("hfacts", "hsettle", "nullsat")),
 ("`tests/seal/model.py:154-172` _all", "what the header proves: every row the chunk holds matches, so none of them null",
  q("hfacts", "hsettle", "nullsat")),
 ("`tests/seal/model.py:174-198` _spread", "the interpolation: the width of the part per condition kind",
  q("spread", "parts")),
 ("`tests/seal/model.py:174-198` _spread", "an empty part counts nothing, or every non-null row for ne",
  q("empty")),
 ("`tests/seal/model.py:174-198` _spread", "the share is rounded up, and ne takes the complement",
  q("round", "spne")),
 ("`tests/seal/model.py:174-198` _spread", "not-null counts the non-null rows and is-null the nulls",
  q("spnn")),
 ("`tests/seal/model.py:228-262` _one setup", "a query starts with every row but the deleted alive and nothing read",
  q("reset", "value")),
 ("`tests/seal/model.py:270-286` score and refresh", "a pending pair, its score and the two tie-breaks",
  q("pending", "choice", "tie")),
 ("`tests/seal/model.py:288-295` strike", "a row that dies leaves one chunk of every column",
  q("part", "die")),
 ("`tests/seal/model.py:297-306` fetch", "a read prints dc and settles every condition of the column over the chunk as written",
  q("rprint", "rsettle", "written")),
 ("`tests/seal/model.py:308-312` charge", "a dictionary is charged once per chunk per query", q("dcharge")),
 ("`tests/seal/model.py:318-332` the choice loop", "the conditions end when nothing is pending",
  q("done")),
 ("`tests/seal/model.py:333-338` rows with an update", "an updated live row is tested on its new value",
  q("value", "moved")),
 ("`tests/seal/model.py:339` nothing held", "no live row takes its value from the chunk: nothing consulted or read",
  q("forheld", "cheap")),
 ("`tests/seal/model.py:340-343` the header decisions", "the header settles the held rows first",
  q("hsettle", "steps")),
 ("`tests/seal/model.py:344-356` the dictionary", "only a dictionary with no literal token, only for a comparison, before a read",
  q("dwhole", "steps")),
 ("`tests/seal/model.py:344-356` the dictionary", "the three verdicts", q("dverdict")),
 ("`tests/seal/model.py:357-360` the read", "a read chunk settles from its values; otherwise the chunk is read and filtered",
  q("steps", "die")),
 ("`tests/seal/model.py:364-368` the digest", "the count and the digest of the surviving rows", q("sel")),
 ("`tests/seal/model.py:370-404` the report pass", "the columns in the order the query names them",
  q("prjorder")),
 ("`tests/seal/model.py:370-392` the report pass", "a chunk is wanted only for a live row taking its value from it",
  q("prjread", "forheld")),
 ("`tests/seal/model.py:370-392` the report pass", "header, then a one-entry dictionary, then a read",
  q("prjread", "costs", "hfacts", "dwhole")),
 ("`tests/seal/model.py:394-404` the report pass", "the two figures on the line, updates applied",
  q("prjline", "value")),
 ("`tests/seal/model.py:408-414` expect", "the query line and its number, and nothing else printed",
  q("qryline")),
]

CASE_ROWS = {
 "hdr-widen-high": ("a widened high bound reaches above the value", q("widen", "hsettle")),
 "hdr-widen-low": ("a widened low bound reaches below the value", q("widen", "hsettle")),
 "hdr-widen-eq": ("a widened pair is not a single value", q("widen", "hsettle")),
 "hdr-widen-ne": ("a widened pair does not rule a value out", q("widen", "hsettle")),
 "hdr-miss-skip": ("a chunk the header rules out is dropped unread", q("hfacts", "hsettle")),
 "hdr-all-pass": ("a chunk the header proves whole is kept unread", q("hfacts", "hsettle")),
 "hdr-nulls-block-pass": ("a chunk holding nulls is never kept unread", q("hsettle", "nullsat")),
 "hdr-ne-exact-miss": ("a one-value chunk under ne is dropped unread", q("hsettle")),
 "hdr-null-chunk-null": ("an all-null chunk under is-null and under is-not-null", q("allnull", "hsettle")),
 "hdr-nu-no-nulls": ("a chunk with no nulls under is-null", q("hsettle", "prjline")),
 "dic-whole-drop": ("no dictionary entry matching drops the chunk", q("dverdict")),
 "dic-whole-keep": ("every entry matching with no nulls keeps it", q("dverdict")),
 "dic-whole-read": ("some entries matching reads it", q("steps", "dverdict")),
 "dic-overflow-read": ("a dictionary with a literal token answers nothing", q("dwhole", "steps")),
 "dic-charge-once": ("a second condition on the same chunk prints no read", q("dcharge")),
 "dic-nulls-read": ("every entry matching but the chunk holds nulls", q("dverdict")),
 "dic-not-for-null": ("is-not-null is never answered from a dictionary", q("dverdict", "steps")),
 "dic-drop-with-nulls": ("a ruled-out chunk is dropped although it holds nulls",
                         q("dverdict", "nullsat")),
 "prj-dead-chunk": ("a reported chunk with no survivor is not read", q("prjread")),
 "prj-listed-order": ("the columns in the order the query names them", q("prjorder")),
 "prj-same-twice": ("a column named twice is reported twice", q("prjorder")),
 "prj-nulls-out": ("nulls are out of both reported figures", q("prjline")),
 "prj-reuse-read": ("a chunk read by a condition is not read again", q("prjread")),
 "ord-nothing-prunes": ("nothing prunes and only the interleaving differs",
                        q("pending", "choice", "tie")),
 "ord-keeps-all": ("every condition keeps everything and nothing is dropped", q("hsettle")),
 "ord-spread-rounds-up": ("the share is rounded up", q("round")),
 "ord-spread-takes-edge": ("the part includes its endpoint", q("parts")),
 "ord-exact-after-read": ("a read chunk is scored by its exact count afterwards",
                          q("rsettle", "choice")),
 "dec-hits-whole-chunk": ("the exact count is over all the chunk's rows", q("rsettle")),
 "qry-starts-over": ("the second query reads what the first already read", q("reset")),
 "sel-empty": ("nothing survives, and the report reads nothing", q("sel", "prjread")),
 "upd-drop-spares": ("a header drop settles only the rows the chunk still supplies",
                     q("moved", "steps", "value")),
 "upd-keep-tests": ("a header keep still tests the updated rows on their own value",
                    q("moved", "steps")),
 "upd-all-moved-no-read": ("a chunk whose live rows all carry updates is not read",
                           q("forheld", "moved")),
 "upd-all-moved-no-rd": ("nor is its dictionary consulted", q("forheld", "cheap")),
 "upd-last-held-dies": ("the last row that needed the chunk died first, so nothing is read",
                        q("forheld", "moved")),
 "upd-count-as-written": ("a read's exact counts ignore updates", q("rsettle", "written")),
 "del-never-alive": ("deleted rows are never alive, so their chunk is never pending",
                     q("value", "pending", "reset")),
 "del-caps-score": ("the cap is the live rows, deleted ones not counted", q("choice", "value")),
 "prj-moved-no-read": ("a reported chunk whose survivors all carry updates is not read",
                       q("prjread", "value")),
 "prj-void-no-read": ("a reported all-null chunk is supplied by its header", q("prjread", "hfacts", "allnull")),
 "prj-pinned-no-read": ("a reported one-value chunk with no nulls is supplied by its header",
                        q("prjread", "hfacts", "exact")),
 "prj-widened-not-pinned": ("a widened recorded pair of one value does not fix the values",
                            q("prjread", "widen")),
 "prj-one-entry-rd": ("a one-entry dictionary with no nulls supplies the values for its charge",
                      q("prjread", "dwhole", "costs", "dknown")),
 "prj-one-entry-nulls": ("a one-entry dictionary with nulls does not fix which rows are null",
                         q("prjread", "dwhole")),
 "ord-read-raises": ("a read can raise a pair's score above what it was", q("rsettle", "choice")),
 "ord-read-rescored": ("a read changes the scores of every condition on that chunk", q("rsettle", "choice")),
}

READINGS = {
 "hdr-bounds-exact": (q("widen"), "hdr-widen-eq"),
 "hdr-pass-ignores-nulls": (q("hsettle", "nullsat"), "hdr-nulls-block-pass"),
 "hdr-null-always-read": (q("hsettle"), "hdr-nu-no-nulls"),
 "hdr-spread-floor": (q("round"), "ord-read-raises"),
 "hdr-spread-open": (q("parts"), "dec-hits-whole-chunk"),
 "dic-overflow-used": (q("dwhole"), "dic-overflow-read"),
 "dic-charge-each": (q("dcharge"), "dic-charge-once"),
 "dic-keep-ignores-nulls": (q("dverdict"), "dic-nulls-read"),
 "dic-answers-null": (q("dverdict"), "dic-not-for-null"),
 "dic-drop-needs-nulls": (q("dverdict", "nullsat"), "dic-drop-with-nulls"),
 "ord-fixed-sweep": (q("pending", "choice"), "ord-nothing-prunes"),
 "ord-column-sum": (q("choice"), "ord-nothing-prunes"),
 "ord-no-cap": (q("choice"), "del-caps-score"),
 "ord-header-only": (q("rsettle", "spread"), "ord-exact-after-read"),
 "ord-highest-chunk": (q("tie"), "dec-hits-whole-chunk"),
 "ord-largest-first": (q("choice"), "dec-hits-whole-chunk"),
 "ord-stale-key": (q("choice", "rsettle"), "ord-read-raises"),
 "ord-read-no-push": (q("choice", "rsettle"), "ord-read-rescored"),
 "dec-one-cond": (q("rsettle"), "ord-exact-after-read"),
 "dec-hits-live-only": (q("rsettle", "written"), "dec-hits-whole-chunk"),
 "upd-drop-takes-moved": (q("moved", "steps"), "upd-drop-spares"),
 "upd-keep-trusts-moved": (q("moved", "steps"), "upd-keep-tests"),
 "upd-read-anyway": (q("forheld", "cheap"), "upd-all-moved-no-rd"),
 "upd-merge-on-read": (q("forheld", "written"), "upd-all-moved-no-rd"),
 "upd-count-current": (q("rsettle", "written"), "upd-count-as-written"),
 "del-still-alive": (q("value", "reset"), "del-caps-score"),
 "del-still-counted": (q("choice", "value"), "del-caps-score"),
 "prj-all-chunks": (q("prjread"), "dic-drop-with-nulls"),
 "prj-reads-moved": (q("prjread"), "prj-moved-no-read"),
 "prj-reads-pinned": (q("prjread", "hfacts"), "prj-pinned-no-read"),
 "prj-pinned-ignores-widen": (q("widen", "prjread"), "prj-one-entry-rd"),
 "prj-no-one-entry": (q("prjread", "costs", "dknown"), "prj-one-entry-rd"),
 "prj-one-entry-free": (q("dcharge", "costs"), "prj-one-entry-rd"),
 "prj-one-entry-with-nulls": (q("prjread", "dwhole"), "prj-one-entry-nulls"),
 "prj-index-order": (q("prjorder"), "prj-listed-order"),
 "prj-nulls-counted": (q("prjline"), "hdr-nu-no-nulls"),
 "prj-redecode": (q("prjread", "costs"), "hdr-nu-no-nulls"),
 "qry-keeps-state": (q("reset"), "del-caps-score"),
}

SHORTCUTS = [
 ("the shipped tree unchanged (the nop)",
  "reward 0 in the two-container trial (the wide files do not finish inside the clock); on the host it matches 17 of 47 hand files and 0 of 308 small generated files"),
 ("a constant: one fixed two-line output for every segment file (`cheat-const-nothing`)",
  "reward 0; matches 0 of 47 hand and 0 of 308 small generated files"),
 ("positional: the conditions in query order over whole columns (`cheat-pos-query-order`)",
  "reward 0; matches 42 of 47 hand files (those with one condition, where query order is the order) and 13 of 308 small generated files"),
 ("the worked example's output replayed for every file (`cheat-replay-example`)",
  "reward 0; matches 0 of 47 and 0 of 308, since tiny.txt is not graded"),
 ("the frozen answers for the enumerated set carried in a collected file (`cheat-forge-hand`)",
  "reward 0; matches all 47 hand files and 0 of the 308 small generated files it could not have seen"),
 ("the previous design's complete reference (`cheat-chunk-is-unit`)",
  "reward 0; fails 12 of 47 hand files and 263 of 308 small generated files, and its rescan loop does not finish the wide files"),
]

TOLERANCES = [
 ("`tests/test.sh:38` the 60 second clock on the graded run",
  "`authoring/scan-chunk-pick/variants/ok-slice` (no maintained survivor counts, version-stamped heap, binary-search chunk lookup) "
  "and `authoring/scan-chunk-pick/variants/ok-tree` (segment tree of exact minima, counts in one dict), both written apart from the reference",
  "whole 361-file graded set in a python:3.12-slim container at 1 CPU and 2 GB: reference 5.3 s, ok-slice 6.1 s, ok-tree 9.6 s, "
  "against 60 s; both variants score 1 in the two-container trial. The naive family the limit rules out is the rescan loop "
  "(`cheat-slow-rescan`): 506 s on one wide file on the host, about 100 s with cached estimates, against 1.3 s for the reference, "
  "with a trace identical to the reference's."),
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
