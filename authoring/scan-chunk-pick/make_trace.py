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
 "layout": "A column is stored as chunks and a chunk as pages, both in row order and together covering every row",
 "numbers": "chunks are numbered from 0 within their column and pages from 0 within their chunk, and the partitions of two columns need not line up",
 "ch": "`ch C p` opens a plain chunk of column C, and `ch C d m e1 ... em` opens one with a dictionary of m entries, ascending.",
 "pg": "Each `pg n u mn mx x s f ...` line after it is a page of that chunk: n rows, u of them null, mn and mx the recorded low and high over the rest, x either `e` or `w`, s the sum of the rest",
 "forms": "f either `v` followed by the n values or `i` followed by n indexes into the dictionary of the chunk, `-` for a null either way. Only a `d` chunk has `i` pages.",
 "upd": "`up C r v` says row r now holds v in column C, `-` for a null, and `del r` says row r was deleted; a row has at most one update per column.",
 "query": "`qry` opens a query, `prd` carries one condition, `prj` names the columns to report and `end` closes it",
 "kinds": "A condition is `ge C v`, `le C v`, `eq C v` or `ne C v` against a value, or `nn C` and `nu C` for not-null and null",
 "nullsat": "A null satisfies `nu` and nothing else.",
 "example": "The seven lines it should print are `qry 0`, `rd 0 0`, `dc 0 0 0`, `sel 4 2000021000077000102`, `dc 1 0 0`, `prj 1 4 16` and `prj 0 4 30`",
 "files": "The files you may change are `/app/scn/hdr.py`, `/app/scn/dct.py`, `/app/scn/live.py`, `/app/scn/pick.py`, `/app/scn/step.py` and `/app/scn/proj.py`. Nothing else.",
 "replaced": "The rest of the tree is replaced by our own copy before a segment file is run, including any new file put beside those six.",
 "entry": "calls `live.fresh` once per file and then `live.start`, `pick.run`, `live.rows` and `proj.run` for each query, so those five keep their names and the arguments they are handed",
 "value": "A row's value in a column is its update when it has one, and what its page holds otherwise. A deleted row is never alive.",
 "written": "Everything a page says about itself describes it as written: its header and the counts a read of it yields. Deleted rows and replaced values are included.",
 "hfacts": "A page header knows three things: u of its rows are null, every other value lies between its bounds, and those values sum to s.",
 "exact": "Under `e` the bounds are the recorded pair.",
 "widen": "Under `w` that pair was rounded inward to a multiple of G, so the bounds are the recorded low less G-1 and the recorded high plus G-1.",
 "allnull": "A page whose rows are all null writes both as `-` and has no bounds.",
 "hsettle": "What the first two facts prove about every row a page holds, its header settles: that a condition fails for all of them, or holds for all of them.",
 "dscope": "Every non-null value on an `i` page is one of the entries of its chunk. So the dictionary can settle a comparison for an `i` page the same way.",
 "dverdict": "No entry satisfying it fails every row; every entry satisfying it, with the page holding no null, passes every row. It says nothing about a `v` page and never settles `nn` or `nu`.",
 "dknown": "How many entries a dictionary has, and which pages are `i`, is known without consulting it.",
 "rprint": "Reading a page prints `dc` with its column, chunk and page numbers, and yields its values; reading an `i` page does not consult the dictionary. Consulting the dictionary of a chunk prints `rd` with its column and chunk.",
 "memory": "A file is scanned with one memory. A page read or a dictionary consulted by any query is known to every query after it in the file, and each prints only the first time.",
 "cheap": "Nothing is consulted or read while something cheaper already answers.",
 "costs": "A header costs nothing. So do a page already read and a dictionary already consulted. A dictionary costs its charge, and a page costs a read.",
 "forheld": "A page is only ever read, or its dictionary consulted, for a live row that takes its value in that column from that page.",
 "moved": "When a condition is applied to a chunk, its live rows that carry an update in that column are tested on that value.",
 "steps": "Then its pages are taken in order. The other live rows of each page are settled by its header if it can, then by a read already made; otherwise, for a comparison on an `i` page, the dictionary is consulted, however little it turns out to settle, before the page is read.",
 "die": "Rows the condition fails die.",
 "rsettle": "Reading a page settles the exact count of every condition of the query over that column on that page, counted over the page as written. A page read before a query starts counts exactly from its start.",
 "spread": "Otherwise the count is the spread of the header.",
 "parts": "the high less v plus one for `ge v`, v less the low plus one for `le v`, and one for `eq v` and `ne v` when v lies within the bounds and none when it does not",
 "empty": "Where it comes out at nothing or less the count is zero for `ge v`, `le v` and `eq v`, and all of the non-null rows of the page for `ne v`.",
 "round": "cut the part down to the width of the bounds, multiply the non-null rows by it, divide by that width and round up",
 "spne": "for `ne v` it is the non-null rows less it",
 "spnn": "`nn` counts the non-null rows, `nu` counts the nulls, and a page with no bounds counts nothing for anything but `nu`.",
 "chunkcount": "The count of a condition on a chunk is the sum of its counts on the pages of that chunk.",
 "pending": "A condition and a chunk of its column are a pending pair while the condition has not been applied to that chunk and the chunk still holds a live row.",
 "choice": "The pair applied next is always the one expected to leave the fewest rows alive. That is the smaller of the live rows that chunk holds and the count of the condition on it.",
 "tie": "A tie goes to the condition written earlier in the query, then to the lower chunk number.",
 "done": "The conditions are done when nothing is pending.",
 "sel": "Then comes `sel`, the number of live rows and a digest of them: start at zero and, for each live row in ascending order, multiply by 1000003, add the row number plus one and take the remainder by 2305843009213693951.",
 "prjorder": "After it every column the query names is reported, in the order it names them and once for each time it names it",
 "prjline": "as `prj`, the column, the count of live rows whose value there is not null, and the sum of those values",
 "prjneed": "What that line needs from a page is how many of the live rows taking their value from it hold a non-null value and what those values sum to.",
 "prjread": "Before the line, every page of the column holding such a row, in chunk and page order, has it answered on the same terms: by a page already read, or by its header when every row of the page is null, when the page holds no null and its bounds are one value, or when those rows are every row of the page; then by consulting the dictionary, for an `i` page holding no null when the dictionary has a single entry; and by a read otherwise.",
 "qryline": "`qry` and the number of the query, counted from 0 within the file, opens each query, and nothing else is printed.",
 "reset": "Every query starts with every row not deleted alive.",
 "wide": "`/app/segs/wide.txt` is sixty thousand rows over five columns, in chunks of sixteen to forty rows and pages of four to twelve, with three queries of eight conditions.",
 "deep": "`/app/segs/deep.txt` is forty thousand rows over four columns in chunks of about two thousand rows and pages of a few hundred, with three queries of seven.",
 "graded": "The graded set is three segment files of each of those two shapes, 308 smaller ones and 60 written by hand.",
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
 ("`tests/test_outputs.py:124` test_the_model_still_reproduces_the_frozen_answers",
  "the sealed model still reproduces the frozen answers; grades nothing by itself",
  q("example")),
 ("`tests/test_outputs.py:134` test_hand_case",
  "every line of every hand-written segment file, in order, against the frozen answers",
  q("qryline", "example", "graded")),
 ("`tests/test_outputs.py:143` test_every_drawn_segment_matches",
  "every line of every generated segment file, in order, against the sealed model",
  q("graded")),
 ("`tests/test_outputs.py:162` test_every_family_is_represented",
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
 ("`tests/seal/model.py:52-105` _read", "the segment grammar: header, chunks and their pages, updates, deletes, queries",
  q("seg", "ch", "pg", "forms", "upd", "query")),
 ("`tests/seal/model.py:52-105` _read", "chunks and pages cover every row in order and two columns need not agree",
  q("layout", "numbers")),
 ("`tests/seal/model.py:107-113` _span", "an exact recorded pair is used as written", q("exact")),
 ("`tests/seal/model.py:107-113` _span", "a widened pair is pushed out by the granularity less one", q("widen")),
 ("`tests/seal/model.py:107-113` _span", "an all-null page has no bounds", q("allnull")),
 ("`tests/seal/model.py:115-130` _holds", "what each condition means on one value", q("kinds", "nullsat")),
 ("`tests/seal/model.py:132-151` _none", "what a page header proves: no row the page holds matches",
  q("hfacts", "hsettle", "nullsat")),
 ("`tests/seal/model.py:153-171` _all", "what a page header proves: every row the page holds matches, so none of them null",
  q("hfacts", "hsettle", "nullsat")),
 ("`tests/seal/model.py:173-197` _spread", "the interpolation: the width of the part per condition kind",
  q("spread", "parts")),
 ("`tests/seal/model.py:173-197` _spread", "an empty part counts nothing, or every non-null row for ne",
  q("empty")),
 ("`tests/seal/model.py:173-197` _spread", "the share is rounded up, and ne takes the complement",
  q("round", "spne")),
 ("`tests/seal/model.py:173-197` _spread", "not-null counts the non-null rows and is-null the nulls",
  q("spnn")),
 ("`tests/seal/model.py:227-254` _one setup", "a query starts with every row but the deleted alive",
  q("reset", "value")),
 ("`tests/seal/model.py:256-279` exact and mark", "a chunk's count sums its pages: exact where read, in this query or earlier, spread otherwise",
  q("rsettle", "spread", "chunkcount", "memory")),
 ("`tests/seal/model.py:281-291` refresh", "a pending pair, its score and the two tie-breaks",
  q("pending", "choice", "tie")),
 ("`tests/seal/model.py:293-300` strike", "a row that dies leaves one chunk of every column",
  q("numbers", "die")),
 ("`tests/seal/model.py:302-307` fetch", "a read prints dc once per file and is remembered",
  q("rprint", "memory", "written")),
 ("`tests/seal/model.py:309-313` charge", "a dictionary is charged once per chunk per file", q("rprint", "memory")),
 ("`tests/seal/model.py:319-332` the choice loop", "the conditions end when nothing is pending",
  q("done")),
 ("`tests/seal/model.py:333-341` rows with an update", "an updated live row is tested on its new value",
  q("value", "moved")),
 ("`tests/seal/model.py:342-343` nothing held", "a page with no live row it still supplies: nothing consulted or read",
  q("forheld", "cheap")),
 ("`tests/seal/model.py:344-348` the header decisions", "a page's header settles the held rows first, pages in order",
  q("hsettle", "steps")),
 ("`tests/seal/model.py:349-359` the dictionary", "only for an `i` page and a comparison, before a read, however little it settles",
  q("dscope", "steps", "dknown")),
 ("`tests/seal/model.py:349-359` the dictionary", "the verdicts, and a null on the page sending it to a read",
  q("dverdict")),
 ("`tests/seal/model.py:360-361` the read", "a page read already settles from its values; otherwise the page is read and filtered",
  q("steps", "die", "costs")),
 ("`tests/seal/model.py:367-371` the digest", "the count and the digest of the surviving rows", q("sel")),
 ("`tests/seal/model.py:373-420` the report pass", "the columns in the order the query names them",
  q("prjorder")),
 ("`tests/seal/model.py:373-393` the report pass", "a page is wanted only for a live row taking its value from it",
  q("prjneed", "prjread", "forheld")),
 ("`tests/seal/model.py:394-419` the report pass", "a page read, then the header (all null, one value, or the whole page's sum), then a one-entry dictionary, then a read",
  q("prjread", "costs", "hfacts", "dscope", "dknown")),
 ("`tests/seal/model.py:373-420` the report pass", "the two figures on the line, updates applied",
  q("prjline", "value")),
 ("`tests/seal/model.py:424-432` expect", "the query line and its number, one memory for the whole file",
  q("qryline", "memory")),
]

CASE_ROWS = {
 "hdr-widen-high": ("a widened high bound reaches above the value", q("widen", "hsettle")),
 "hdr-widen-low": ("a widened low bound reaches below the value", q("widen", "hsettle")),
 "hdr-widen-eq": ("a widened pair is not a single value", q("widen", "hsettle")),
 "hdr-widen-ne": ("a widened pair does not rule a value out", q("widen", "hsettle")),
 "hdr-miss-skip": ("a page the header rules out is dropped unread", q("hfacts", "hsettle")),
 "hdr-all-pass": ("a page the header proves whole is kept unread", q("hfacts", "hsettle")),
 "hdr-nulls-block-pass": ("a page holding nulls is never kept unread", q("hsettle", "nullsat")),
 "hdr-ne-exact-miss": ("a one-value page under ne is dropped unread", q("hsettle")),
 "hdr-null-chunk-null": ("an all-null page under is-null and under is-not-null, and a second query reading nothing twice", q("allnull", "hsettle", "memory")),
 "hdr-nu-no-nulls": ("a page with no nulls under is-null", q("hsettle", "prjline")),
 "dic-whole-drop": ("no dictionary entry matching drops the page", q("dverdict")),
 "dic-whole-keep": ("every entry matching with no nulls keeps it", q("dverdict")),
 "dic-whole-read": ("some entries matching reads it", q("steps", "dverdict")),
 "dic-overflow-read": ("a page that fell back to plain values is outside its dictionary", q("dscope", "dverdict")),
 "dic-charge-once": ("a second condition on the same chunk prints no read", q("rprint", "memory")),
 "dic-nulls-read": ("every entry matching but the page holds nulls", q("dverdict")),
 "dic-not-for-null": ("is-not-null is never answered from a dictionary", q("dverdict", "steps")),
 "dic-drop-with-nulls": ("a ruled-out page is dropped although it holds nulls",
                         q("dverdict", "nullsat")),
 "prj-dead-chunk": ("a reported page with no live row is not read", q("prjread")),
 "prj-listed-order": ("the columns in the order the query names them", q("prjorder")),
 "prj-same-twice": ("a column named twice is reported twice", q("prjorder")),
 "prj-nulls-out": ("nulls are out of both reported figures", q("prjline", "prjneed")),
 "prj-reuse-read": ("a page read by a condition is not read again", q("prjread", "memory")),
 "ord-nothing-prunes": ("nothing prunes and only the interleaving differs",
                        q("pending", "choice", "tie")),
 "ord-keeps-all": ("every condition keeps everything, and whole pages answer from their sums", q("hsettle", "prjread")),
 "ord-spread-rounds-up": ("the share is rounded up", q("round")),
 "ord-spread-takes-edge": ("the part includes its endpoint", q("parts")),
 "ord-exact-after-read": ("a read page is counted exactly afterwards",
                          q("rsettle", "choice")),
 "dec-hits-whole-chunk": ("the exact count is over all the page's rows", q("rsettle")),
 "qry-starts-over": ("the second query reads and charges nothing the first did", q("memory", "reset")),
 "sel-empty": ("nothing survives, and the report reads nothing", q("sel", "prjread")),
 "upd-drop-spares": ("a header drop settles only the rows the page still supplies",
                     q("moved", "steps", "value")),
 "upd-keep-tests": ("a header keep still tests the updated rows on their own value",
                    q("moved", "steps")),
 "upd-all-moved-no-read": ("a page whose live rows all carry updates is not read",
                           q("forheld", "moved")),
 "upd-all-moved-no-rd": ("nor is its dictionary consulted", q("forheld", "cheap")),
 "upd-last-held-dies": ("the last row that needed the page died first, so nothing is read",
                        q("forheld", "moved")),
 "upd-count-as-written": ("a read's exact counts ignore updates", q("rsettle", "written")),
 "del-never-alive": ("deleted rows are never alive, so their chunk is never pending",
                     q("value", "pending", "reset")),
 "del-caps-score": ("the cap is the live rows, deleted ones not counted", q("choice", "value")),
 "prj-moved-no-read": ("a reported page whose survivors all carry updates is not read",
                       q("prjread", "value")),
 "prj-void-no-read": ("a reported all-null page is answered by its header", q("prjread", "allnull")),
 "prj-pinned-no-read": ("a reported one-value page with no nulls is answered by its header",
                        q("prjread", "exact")),
 "prj-widened-not-pinned": ("a widened recorded pair of one value does not fix the values",
                            q("prjread", "widen")),
 "prj-one-entry-rd": ("a one-entry dictionary with no nulls answers for its charge",
                      q("prjread", "dscope", "costs")),
 "prj-one-entry-nulls": ("a one-entry dictionary does not answer a page holding a null",
                         q("prjread")),
 "ord-read-raises": ("a read can raise a pair's score above what it was", q("rsettle", "choice")),
 "ord-read-rescored": ("a read changes the scores of every condition on that chunk", q("rsettle", "choice")),
 "pg-partial-read": ("only the page the header cannot settle is read", q("steps", "cheap")),
 "pg-dict-skips-fallback": ("the dictionary settles its index page and the fallback page is read",
                            q("dscope", "dverdict", "steps")),
 "pg-dict-keep-page-nulls": ("an all-matching dictionary keeps a page with no null and reads one holding a null",
                             q("dverdict")),
 "pg-count-mixed": ("a chunk read in part counts exactly on its read page and by spread on the rest",
                    q("rsettle", "chunkcount", "choice")),
 "mem-no-reread": ("a page read by one query is not read by the next", q("memory")),
 "mem-exact-from-start": ("a page read by an earlier query counts exactly from the start of the next",
                          q("rsettle", "choice")),
 "mem-charge-once-file": ("a dictionary charged in one query is not charged in the next", q("memory")),
 "mem-charge-across": ("a dictionary consulted with no read is still not charged again later", q("memory", "dverdict")),
 "mem-report-read-kept": ("a page the report pass read serves the next query's conditions", q("memory", "costs")),
 "prj-whole-page-sum": ("a reported page whose rows are all wanted is answered by its sum", q("prjread", "hfacts")),
 "prj-whole-broken-by-delete": ("a deleted row means the wanted rows are not every row of the page",
                                q("prjread", "written", "value")),
 "prj-whole-broken-by-update": ("an updated row means the wanted rows are not every row of the page",
                                q("prjread", "prjneed")),
 "prj-one-entry-fallback": ("a one-entry dictionary does not answer a fallback page",
                            q("prjread", "dscope")),
}

READINGS = {
 "hdr-bounds-exact": (q("widen"), "hdr-widen-eq"),
 "hdr-pass-ignores-nulls": (q("hsettle", "nullsat"), "hdr-nulls-block-pass"),
 "hdr-null-always-read": (q("hsettle"), "hdr-nu-no-nulls"),
 "hdr-spread-floor": (q("round"), "ord-read-raises"),
 "hdr-spread-open": (q("parts"), "dec-hits-whole-chunk"),
 "dic-fallback-used": (q("dscope", "dverdict"), "dic-overflow-read"),
 "dic-charge-each": (q("rprint", "memory"), "dic-charge-once"),
 "dic-keep-ignores-nulls": (q("dverdict"), "dic-nulls-read"),
 "dic-answers-null": (q("dverdict"), "dic-not-for-null"),
 "dic-drop-needs-nulls": (q("dverdict", "nullsat"), "dic-drop-with-nulls"),
 "pg-dict-all-pages": (q("dscope", "dknown"), "pg-dict-skips-fallback"),
 "pg-dict-keep-chunk-nulls": (q("dverdict"), "pg-dict-keep-page-nulls"),
 "pg-whole-chunk-read": (q("steps", "forheld", "cheap"), "pg-count-mixed"),
 "pg-count-all-or-nothing": (q("rsettle", "chunkcount"), "pg-count-mixed"),
 "pg-read-consults-dict": (q("rprint", "costs"), "dic-not-for-null"),
 "ord-fixed-sweep": (q("pending", "choice"), "mem-exact-from-start"),
 "ord-column-sum": (q("choice"), "ord-nothing-prunes"),
 "ord-no-cap": (q("choice"), "del-caps-score"),
 "ord-header-only": (q("rsettle", "spread"), "mem-exact-from-start"),
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
 "mem-none": (q("memory"), "hdr-null-chunk-null"),
 "mem-no-exact-start": (q("rsettle"), "mem-exact-from-start"),
 "mem-charge-per-query": (q("memory"), "mem-charge-across"),
 "mem-report-not-kept": (q("memory"), "hdr-null-chunk-null"),
 "prj-all-pages": (q("prjread"), "dic-drop-with-nulls"),
 "prj-reads-moved": (q("prjread", "prjneed"), "prj-moved-no-read"),
 "prj-reads-pinned": (q("prjread", "hfacts"), "prj-pinned-no-read"),
 "prj-pinned-ignores-widen": (q("widen", "prjread"), "prj-one-entry-fallback"),
 "prj-no-whole-sum": (q("prjread", "hfacts"), "dic-whole-keep"),
 "prj-whole-ignores-deletes": (q("prjread", "written", "value"), "del-never-alive"),
 "prj-whole-ignores-updates": (q("prjread", "prjneed"), "prj-whole-broken-by-update"),
 "prj-no-one-entry": (q("prjread", "costs", "dknown"), "prj-one-entry-rd"),
 "prj-one-entry-with-nulls": (q("prjread"), "prj-one-entry-nulls"),
 "prj-one-entry-fallback": (q("prjread", "dscope"), "prj-one-entry-fallback"),
 "prj-one-entry-free": (q("rprint", "costs"), "prj-one-entry-rd"),
 "prj-index-order": (q("prjorder"), "prj-listed-order"),
 "prj-nulls-counted": (q("prjline"), "hdr-nu-no-nulls"),
 "prj-redecode": (q("prjread", "costs"), "hdr-nu-no-nulls"),
}

SHORTCUTS = [
 ("the shipped tree unchanged (the nop)",
  "reward 0; on the host it matches 9 of 60 hand files and 0 of 308 small generated files"),
 ("a constant: one fixed two-line output for every segment file (`cheat-const-nothing`)",
  "reward 0; matches 0 of 60 hand and 0 of 308 small generated files"),
 ("positional: the conditions in query order over whole columns (`cheat-pos-query-order`)",
  "reward 0; matches 53 of 60 hand files (those with one condition, where query order is the order) and 2 of 308 small generated files"),
 ("the worked example's output replayed for every file (`cheat-replay-example`)",
  "reward 0; matches 0 of 60 and 0 of 308, since tiny.txt is not graded"),
 ("the frozen answers for the enumerated set carried in a collected file, keyed on each file's query history (`cheat-forge-hand`)",
  "reward 0; matches all 60 hand files and 0 of the 308 small generated files it could not have seen"),
 ("the previous design of this engine (`cheat-chunk-is-unit`)",
  "reward 0; matches 34 of 60 hand files and 7 of 308 small generated files"),
]

TOLERANCES = [
 ("`tests/test.sh:38` the 60 second clock on the graded run",
  "`authoring/scan-chunk-pick/variants/ok-slice` (no maintained counts, version-stamped heap, binary-search chunk lookup) "
  "and `authoring/scan-chunk-pick/variants/ok-tree` (segment tree of exact minima, chunk counts summed afresh from pages), both written apart from the reference",
  "whole 374-file graded set in a python:3.12-slim container at 1 CPU and 2 GB: reference 8.2 s, ok-slice 10.8 s, ok-tree 12.9 s, "
  "against 60 s. The naive family the limit rules out is the rescan loop (`cheat-slow-rescan`): 142.5 s on one wide file on "
  "the host against 2.1 s for the reference, with a trace identical to the reference's."),
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
