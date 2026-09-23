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
 "ch": "`ch C p s` opens a plain chunk of column C, and `ch C d s m e1 ... em` opens one with a dictionary of m entries, ascending; s is the sum of the non-null values its pages hold.",
 "pg": "Each `pg n u mn mx x f ...` line after it is a page of that chunk: n rows, u of them null, mn and mx the recorded low and high over the rest, x either `e` or `w`",
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
 "written": "Everything a page or a chunk says about itself describes it as written: its header, its sum and the counts a read of it yields. Deleted rows and replaced values are included.",
 "hfacts": "A page header knows two things: u of its rows are null, and every other value lies between its bounds.",
 "exact": "Under `e` the bounds are the recorded pair.",
 "widen": "Under `w` that pair was rounded inward to a multiple of G, so the bounds are the recorded low less G-1 and the recorded high plus G-1.",
 "allnull": "A page whose rows are all null writes both as `-` and has no bounds.",
 "hsettle": "What these prove about every row a page holds, its header settles: that a condition fails for all of them, or holds for all of them.",
 "dscope": "Every non-null value on an `i` page is one of the entries of its chunk. So the dictionary, once consulted, settles a comparison for an `i` page the same way.",
 "dverdict": "No entry satisfying it fails every row; every entry satisfying it, with the page holding no null, passes every row. It says nothing about a `v` page and never settles `nn` or `nu`.",
 "dknown": "How many entries a dictionary has, and which pages are `i`, is known without consulting it.",
 "rprint": "Reading a page prints `dc` with its column, chunk and page numbers, and yields its values; reading an `i` page does not consult the dictionary. Consulting the dictionary of a chunk prints `rd` with its column and chunk.",
 "memory": "A file is scanned with one memory. A page read or a dictionary consulted by any query is known to every query after it, and each prints only the first time.",
 "known": "What is known of a row's value in a column is its update when it has one, and otherwise its page's header, the page's values once read, and for an `i` page its chunk's dictionary once consulted.",
 "dies": "A row dies the moment what is known shows that it fails a condition of the query. A condition is settled for a row once what is known shows whether the row satisfies it.",
 "pending": "A condition and a chunk of its column are a pending pair while a live row takes its value from one of the chunk's pages without the condition settled for it.",
 "apply": "Applying a pair takes the chunk's pages in order. For each page still holding such a row, a comparison on an `i` page whose dictionary is not yet consulted consults it first, however little it turns out to settle. Then, if such a row remains, the page is read.",
 "rsettle": "Reading a page settles the exact count of every condition of the query over that column on that page, counted over the page as written. A page read before a query starts counts exactly from its start.",
 "spread": "Otherwise the count is the spread of the header.",
 "parts": "the high less v plus one for `ge v`, v less the low plus one for `le v`, and one for `eq v` and `ne v` when v lies within the bounds and none when it does not",
 "empty": "Where it comes out at nothing or less the count is zero for `ge v`, `le v` and `eq v`, and all of the non-null rows of the page for `ne v`.",
 "round": "cut the part down to the width of the bounds, multiply the non-null rows by it, divide by that width and round up",
 "spne": "for `ne v` it is the non-null rows less it",
 "spnn": "`nn` counts the non-null rows, `nu` counts the nulls, and a page with no bounds counts nothing for anything but `nu`.",
 "chunkcount": "The count of a condition on a chunk is the sum of its counts on the pages of that chunk.",
 "choice": "The pair applied next is always the one expected to leave the fewest rows alive. That is the smaller of the live rows that chunk holds and the count of the condition on it.",
 "tie": "A tie goes to the condition written earlier in the query, then to the lower chunk number.",
 "done": "The conditions are done when nothing is pending.",
 "sel": "Then comes `sel`, the number of live rows and a digest of them: start at zero and, for each live row in ascending order, multiply by 1000003, add the row number plus one and take the remainder by 2305843009213693951.",
 "prjorder": "After it every column the query names is reported, in the order it names them and once for each time it names it",
 "prjline": "as `prj`, the column, the count of live rows whose value there is not null, and the sum of those values",
 "supplies": "The rows a page supplies there are the live rows that take their value in that column from it.",
 "prjread": "The report reads a page only for rows it supplies. It reads one only when the line could not be worked out without it, even if every other page it could read were read.",
 "prjknown": "To work it out there is what is known: the values of a page once read; that every non-null value of a page is its low, when its bounds are one value, or the entry, when it is an `i` page of a chunk whose dictionary has a single entry and is known; how many rows of each page are null; and the sum of each chunk.",
 "prjconsult": "Before a chunk's reads the report consults its dictionary when that has a single entry, one of its `i` pages supplies a row, and knowing it would spare a read. It consults no other.",
 "prjorderreads": "Its reads come in chunk and page order.",
 "qryline": "`qry` and the number of the query, counted from 0 within the file, opens each query, and nothing else is printed.",
 "reset": "Every query starts with every row not deleted alive.",
 "wide": "`/app/segs/wide.txt` is sixty thousand rows over five columns, in chunks of sixteen to forty rows and pages of four to twelve, with three queries of eight conditions.",
 "deep": "`/app/segs/deep.txt` is forty thousand rows over four columns in chunks of about two thousand rows and pages of a few hundred, with three queries of seven.",
 "graded": "The graded set is three segment files of each of those two shapes, 330 smaller ones and 82 written by hand.",
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
 ("`tests/test_outputs.py:133` test_the_model_still_reproduces_the_frozen_answers",
  "the sealed model still reproduces the frozen answers; grades nothing by itself",
  q("example")),
 ("`tests/test_outputs.py:143` test_hand_case",
  "every line of every hand-written segment file, in order, against the frozen answers",
  q("qryline", "example", "graded")),
 ("`tests/test_outputs.py:152` test_every_drawn_segment_matches",
  "every line of every generated segment file, in order, against the sealed model",
  q("graded")),
 ("`tests/test_outputs.py:171` test_every_family_is_represented",
  "that the generated population covers all seventeen families",
  q("graded")),
 ("artifact `/app/scn/hdr.py`", "only the declared files are collected", q("files", "replaced")),
 ("artifact `/app/scn/dct.py`", "only the declared files are collected", q("files", "replaced")),
 ("artifact `/app/scn/live.py`", "only the declared files are collected", q("files", "replaced")),
 ("artifact `/app/scn/pick.py`", "only the declared files are collected", q("files", "replaced")),
 ("artifact `/app/scn/step.py`", "only the declared files are collected", q("files", "replaced")),
 ("artifact `/app/scn/proj.py`", "only the declared files are collected", q("files", "replaced")),
 ("`tests/test.sh:38` a 60 s clock", "the whole graded set inside one wall clock, one process, standard library",
  q("limit", "wide", "deep")),
 ("`tests/worker.py:38` the collected files laid over a pristine tree",
  "a seventh file beside the six is never collected, and the driver's entry points are fixed",
  q("replaced", "entry")),
 ("`tests/seal/model.py:55-109` _read", "the segment grammar: header, chunks with their sums and their pages, updates, deletes, queries",
  q("seg", "ch", "pg", "forms", "upd", "query")),
 ("`tests/seal/model.py:55-109` _read", "chunks and pages cover every row in order and two columns need not agree",
  q("layout", "numbers")),
 ("`tests/seal/model.py:111-116` _span", "an exact recorded pair is used as written", q("exact")),
 ("`tests/seal/model.py:111-116` _span", "a widened pair is pushed out by the granularity less one", q("widen")),
 ("`tests/seal/model.py:111-116` _span", "an all-null page has no bounds", q("allnull")),
 ("`tests/seal/model.py:119-133` _holds", "what each condition means on one value", q("kinds", "nullsat")),
 ("`tests/seal/model.py:136-154` _none", "what a page header proves: no row the page holds matches",
  q("hfacts", "hsettle", "nullsat")),
 ("`tests/seal/model.py:157-174` _all", "what a page header proves: every row the page holds matches, so none of them null",
  q("hfacts", "hsettle", "nullsat")),
 ("`tests/seal/model.py:177-200` _spread", "the interpolation: the width of the part per condition kind",
  q("spread", "parts")),
 ("`tests/seal/model.py:177-200` _spread", "an empty part counts nothing, or every non-null row for ne",
  q("empty")),
 ("`tests/seal/model.py:177-200` _spread", "the share is rounded up, and ne takes the complement",
  q("round", "spne")),
 ("`tests/seal/model.py:177-200` _spread", "not-null counts the non-null rows and is-null the nulls",
  q("spnn")),
 ("`tests/seal/model.py:231-261` _one setup", "a query starts with every row but the deleted alive",
  q("reset", "value")),
 ("`tests/seal/model.py:263-283` fate", "what is known of a row's value: its update, its page's header, its page's values once read, its chunk's dictionary once consulted",
  q("known", "value", "hsettle", "dscope", "dverdict")),
 ("`tests/seal/model.py:285-306` strike and sweep", "a row dies the moment what is known fails it, on any condition, from the start of the query",
  q("dies", "known")),
 ("`tests/seal/model.py:308-318` left and waiting", "a pair is pending while a live row takes its value from its pages unsettled",
  q("pending", "choice")),
 ("`tests/seal/model.py:320-333` exact and mark", "a chunk's count sums its pages: exact where read, in this query or earlier, spread otherwise",
  q("rsettle", "spread", "chunkcount", "memory")),
 ("`tests/seal/model.py:335-350` refresh", "a pending pair's score and the two tie-breaks",
  q("choice", "tie")),
 ("`tests/seal/model.py:352-357` fetch", "a read prints dc once per file and is remembered",
  q("rprint", "memory", "written")),
 ("`tests/seal/model.py:359-364` charge", "a dictionary is charged once per chunk per file", q("rprint", "memory")),
 ("`tests/seal/model.py:371-399` the choice loop", "the conditions end when nothing is pending",
  q("done")),
 ("`tests/seal/model.py:379-395` applying a pair", "pages in order; the dictionary first for a comparison on an `i` page, however little it settles; a read if an unsettled row remains",
  q("apply", "dscope", "dknown")),
 ("`tests/seal/model.py:390-395` after a consult or a read", "what was learned acts at once on every condition over the column",
  q("dies", "rsettle")),
 ("`tests/seal/model.py:401-405` the digest", "the count and the digest of the surviving rows", q("sel")),
 ("`tests/seal/model.py:407-435` figures", "what tells the line: pages read, all-null pages, one-value pages, a known one-entry dictionary, null counts and chunk sums",
  q("prjknown", "written")),
 ("`tests/seal/model.py:437-456` readable and owed", "a page is read only for rows it supplies and only when the line cannot be worked out without it",
  q("supplies", "prjread")),
 ("`tests/seal/model.py:464-473` the report's consult", "a one-entry dictionary is consulted only for a supplied row and only when that spares a read",
  q("prjconsult")),
 ("`tests/seal/model.py:474-475` the report's reads", "reads in chunk and page order", q("prjorderreads")),
 ("`tests/seal/model.py:458-525` the report pass", "the columns in the order the query names them, and the two figures on the line, updates applied",
  q("prjorder", "prjline", "value")),
 ("`tests/seal/model.py:528-536` expect", "the query line and its number, one memory for the whole file",
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
 "dic-whole-read": ("some entries matching reads it", q("apply", "dverdict")),
 "dic-overflow-read": ("a page that fell back to plain values is outside its dictionary", q("dscope", "dverdict")),
 "dic-charge-once": ("a second condition on the same chunk prints no second consult", q("rprint", "memory")),
 "dic-nulls-read": ("every entry matching but the page holds nulls", q("dverdict")),
 "dic-not-for-null": ("is-not-null is never answered from a dictionary", q("dverdict", "apply")),
 "dic-drop-with-nulls": ("a ruled-out page is dropped although it holds nulls", q("dverdict", "nullsat")),
 "prj-dead-chunk": ("a reported page with no live row is not read", q("prjread", "supplies")),
 "prj-listed-order": ("the columns in the order the query names them", q("prjorder")),
 "prj-same-twice": ("a column named twice is reported twice", q("prjorder")),
 "prj-nulls-out": ("nulls are out of both reported figures", q("prjline")),
 "prj-reuse-read": ("a page read by a condition is not read again", q("prjknown", "memory")),
 "ord-nothing-prunes": ("nothing prunes and only the interleaving differs", q("pending", "choice", "tie")),
 "ord-keeps-all": ("every condition keeps everything, and the chunk sums answer the report", q("hsettle", "prjknown")),
 "ord-spread-rounds-up": ("the share is rounded up", q("round")),
 "ord-spread-takes-edge": ("the part includes its endpoint", q("parts")),
 "ord-exact-after-read": ("a read page is counted exactly afterwards", q("rsettle", "choice")),
 "dec-hits-whole-chunk": ("a read settles every condition over its column at once", q("rsettle", "dies")),
 "qry-starts-over": ("the second query reads and charges nothing the first did", q("memory", "reset")),
 "sel-empty": ("nothing survives, and the report reads nothing", q("sel", "prjread")),
 "upd-drop-spares": ("a header drop settles only the rows the page still supplies", q("known", "value")),
 "upd-keep-tests": ("a header keep does not pass the updated rows, their own values do", q("known", "value")),
 "upd-all-moved-no-read": ("a page whose live rows all carry updates is not read", q("pending", "known")),
 "upd-all-moved-no-rd": ("nor is its dictionary consulted", q("pending", "apply")),
 "upd-last-held-dies": ("the last row that needed the page died first, so nothing is read", q("pending", "apply")),
 "upd-count-as-written": ("a read's exact counts ignore updates", q("rsettle", "written")),
 "del-never-alive": ("deleted rows are never alive, so their chunk is never pending", q("value", "pending", "reset")),
 "del-caps-score": ("the cap is the live rows, deleted ones not counted", q("choice", "value")),
 "prj-moved-no-read": ("a reported page whose survivors all carry updates is not read", q("prjread", "supplies")),
 "prj-void-no-read": ("a reported all-null page is not read", q("prjknown", "allnull")),
 "prj-pinned-no-read": ("a reported one-value page with no nulls is not read", q("prjknown", "exact")),
 "prj-widened-not-pinned": ("a widened recorded pair of one value does not fix the values", q("prjknown", "widen")),
 "prj-one-entry-rd": ("a one-entry dictionary is consulted when that spares a read", q("prjconsult", "prjknown")),
 "prj-one-entry-nulls": ("a page holding a null is read whatever its one-entry dictionary says", q("prjknown", "prjread")),
 "ord-read-raises": ("a read can raise a pair's score above what it was", q("rsettle", "choice")),
 "ord-read-rescored": ("a read changes the scores of every condition on that chunk", q("rsettle", "choice")),
 "pg-partial-read": ("only the page the header cannot settle is read", q("apply", "hsettle")),
 "pg-dict-skips-fallback": ("the dictionary settles its index page and the fallback page is read", q("dscope", "dverdict", "apply")),
 "pg-dict-keep-page-nulls": ("an all-matching dictionary keeps a page with no null and reads one holding a null", q("dverdict")),
 "pg-count-mixed": ("a chunk read in part counts exactly on its read page and by spread on the rest", q("rsettle", "chunkcount", "choice")),
 "mem-no-reread": ("a page read by one query is not read by the next", q("memory")),
 "mem-exact-from-start": ("a page read by an earlier query counts exactly from the start of the next", q("rsettle", "choice")),
 "mem-charge-once-file": ("a dictionary charged in one query is not charged in the next", q("memory")),
 "mem-charge-across": ("a dictionary consulted with no read is still not charged again later", q("memory", "dverdict")),
 "mem-report-read-kept": ("a page the report pass read serves the next query's conditions", q("memory", "known")),
 "prj-dead-page-blocks-sum": ("a page with no live row and an unknown sum stops the chunk's sum answering a wholly live page", q("prjread", "prjknown")),
 "prj-whole-broken-by-delete": ("a deleted row means a page's rows are not all live", q("supplies", "value", "written")),
 "prj-whole-broken-by-update": ("an updated row means a page does not supply all its rows", q("supplies", "prjread")),
 "prj-one-entry-fallback": ("a one-entry dictionary tells nothing about a fallback page", q("prjknown", "dscope")),
 "flt-header-kills-at-start": ("a header fails rows for one condition before another condition's pair reads them", q("dies", "known")),
 "flt-header-kills-other-column": ("a header on one column kills rows another column's pair would have read for", q("dies", "known", "pending")),
 "flt-memory-kills-at-start": ("a page remembered from an earlier query kills rows at the start of the next", q("dies", "known", "memory")),
 "flt-dict-settles-every-page": ("a consulted dictionary settles every index page of its chunk at once, for every comparison", q("dies", "dscope", "dverdict")),
 "flt-consult-settles-whole-chunk": ("a consult made for one page settles the chunk's other index pages before any pair reaches them", q("dies", "dscope")),
 "prj-chunk-sum-whole": ("pages whose rows are all live are told by their chunk's sum", q("prjread", "prjknown")),
 "prj-chunk-sum-blocked": ("a dead page with an unknown sum sends the wholly live pages to a read", q("prjread", "prjknown")),
 "prj-chunk-sum-pinned-dead": ("a dead one-value page holding nulls still has a known sum", q("prjknown", "hfacts")),
 "prj-chunk-sum-together": ("several wholly live pages are told together, none of them read", q("prjread", "prjknown")),
 "prj-pinned-nulls-sum": ("a one-value index page holding a null has a known sum", q("prjknown")),
 "prj-reads-in-page-order": ("the report's reads come in chunk and page order", q("prjorderreads")),
 "prj-chunk-sum-update": ("an updated row keeps its page from being wholly live, and the others are still told", q("supplies", "prjknown")),
 "prj-consult-needs-live-row": ("no consult for a dictionary whose index pages supply no row", q("prjconsult")),
 "prj-consult-spares-read": ("a consult that spares reads is made, before the chunk's reads", q("prjconsult", "prjknown")),
 "prj-consult-not-sparing": ("no consult when knowing the entry would spare no read", q("prjconsult")),
 "dec-hits-over-page": ("a read's exact count is over every row of the page as written", q("rsettle", "written")),
 "mem-counts-exact-from-start": ("a remembered page counts exactly from the start of a later query", q("rsettle", "memory")),
 "ord-read-counts-exact": ("a read page counts exactly on the chunk's other pages' spreads", q("rsettle", "chunkcount")),
 "upd-count-over-page-as-written": ("exact counts are over the page as written, an updated row's old value included", q("rsettle", "written")),
 "upd-read-not-merged": ("a read yields the page as written, not merged with updates", q("rprint", "value")),
 "ord-read-raises-repush": ("a read that raises a pending pair's score sends it to be chosen again", q("rsettle", "choice")),
 "ord-read-raises-stale": ("the order uses the raised score, not the one before the read", q("rsettle", "choice", "tie")),
}

READINGS = {
 "hdr-bounds-exact": (q("widen"), "hdr-widen-eq"),
 "hdr-pass-ignores-nulls": (q("hsettle", "nullsat"), "hdr-nulls-block-pass"),
 "hdr-null-always-read": (q("hsettle"), "hdr-nu-no-nulls"),
 "hdr-spread-floor": (q("round"), "ord-spread-rounds-up"),
 "hdr-spread-open": (q("parts"), "ord-spread-takes-edge"),
 "dic-fallback-used": (q("dscope", "dverdict"), "dic-overflow-read"),
 "dic-charge-each": (q("rprint", "memory"), "dic-charge-once"),
 "dic-keep-ignores-nulls": (q("dverdict"), "dic-nulls-read"),
 "dic-answers-null": (q("dverdict"), "dic-not-for-null"),
 "dic-drop-needs-nulls": (q("dverdict", "nullsat"), "dic-drop-with-nulls"),
 "pg-dict-all-pages": (q("dscope", "dknown"), "pg-dict-skips-fallback"),
 "pg-dict-keep-chunk-nulls": (q("dverdict"), "pg-dict-keep-page-nulls"),
 "pg-whole-chunk-read": (q("apply"), "pg-partial-read"),
 "pg-count-all-or-nothing": (q("rsettle", "chunkcount"), "ord-read-counts-exact"),
 "pg-read-consults-dict": (q("rprint"), "dic-not-for-null"),
 "flt-free-when-applied": (q("dies", "known"), "flt-header-kills-other-column"),
 "flt-header-late": (q("dies", "known"), "flt-header-kills-at-start"),
 "flt-memory-late": (q("dies", "memory"), "flt-memory-kills-at-start"),
 "flt-updates-late": (q("dies", "known", "value"), "upd-drop-spares"),
 "flt-read-own-cond": (q("dies", "rsettle"), "dec-hits-whole-chunk"),
 "flt-dict-lazy": (q("dies", "dscope"), "flt-dict-settles-every-page"),
 "flt-dict-one-page": (q("dies", "dscope"), "flt-consult-settles-whole-chunk"),
 "ord-fixed-sweep": (q("pending", "choice"), "mem-exact-from-start"),
 "ord-column-sum": (q("choice"), "ord-nothing-prunes"),
 "ord-no-cap": (q("choice"), "del-caps-score"),
 "ord-header-only": (q("rsettle", "spread"), "mem-counts-exact-from-start"),
 "ord-highest-chunk": (q("tie"), "ord-read-raises-stale"),
 "ord-largest-first": (q("choice"), "dec-hits-over-page"),
 "ord-stale-key": (q("choice", "rsettle"), "ord-read-raises-stale"),
 "ord-read-no-push": (q("choice", "rsettle"), "ord-read-raises-repush"),
 "dec-one-cond": (q("rsettle"), "ord-read-raises-stale"),
 "dec-hits-live-only": (q("rsettle", "written"), "dec-hits-over-page"),
 "upd-drop-takes-moved": (q("known", "value"), "upd-drop-spares"),
 "upd-keep-trusts-moved": (q("known", "value"), "upd-keep-tests"),
 "upd-read-anyway": (q("pending", "apply"), "upd-all-moved-no-rd"),
 "upd-merge-on-read": (q("rprint", "written"), "upd-read-not-merged"),
 "upd-count-current": (q("rsettle", "written"), "upd-count-over-page-as-written"),
 "del-still-alive": (q("value", "reset"), "del-caps-score"),
 "del-still-counted": (q("choice", "value"), "del-caps-score"),
 "mem-none": (q("memory"), "hdr-null-chunk-null"),
 "mem-no-exact-start": (q("rsettle"), "mem-counts-exact-from-start"),
 "mem-charge-per-query": (q("memory"), "mem-charge-across"),
 "mem-report-not-kept": (q("memory"), "mem-report-read-kept"),
 "prj-all-pages": (q("prjread", "supplies"), "prj-dead-chunk"),
 "prj-reads-moved": (q("prjread", "supplies"), "prj-moved-no-read"),
 "prj-reads-pinned": (q("prjknown"), "prj-pinned-no-read"),
 "prj-pinned-ignores-widen": (q("widen", "prjknown"), "prj-widened-not-pinned"),
 "prj-no-chunk-sum": (q("prjknown", "prjread"), "prj-chunk-sum-whole"),
 "prj-last-page-only": (q("prjread"), "prj-chunk-sum-together"),
 "prj-dead-pages-ignored": (q("prjknown", "ch"), "prj-chunk-sum-blocked"),
 "prj-pinned-nulls-unknown": (q("prjknown"), "prj-pinned-nulls-sum"),
 "prj-dict-ignored": (q("prjknown"), "prj-consult-spares-read"),
 "prj-consult-always": (q("prjconsult"), "prj-consult-not-sparing"),
 "prj-consult-never": (q("prjconsult"), "prj-consult-spares-read"),
 "prj-consult-for-dead": (q("prjconsult"), "prj-consult-needs-live-row"),
 "prj-need-first": (q("prjorderreads"), "prj-reads-in-page-order"),
 "prj-whole-ignores-deletes": (q("supplies", "value"), "prj-whole-broken-by-delete"),
 "prj-whole-ignores-updates": (q("supplies"), "prj-chunk-sum-update"),
 "prj-index-order": (q("prjorder"), "prj-listed-order"),
 "prj-nulls-counted": (q("prjline"), "prj-nulls-out"),
 "prj-redecode": (q("prjknown", "prjread"), "prj-reuse-read"),
}

SHORTCUTS = [
 ("the shipped tree unchanged (the nop)",
  "reward 0; on the host it matches 8 of 82 hand files and 0 of 330 small generated files"),
 ("a constant: one fixed two-line output for every segment file (`cheat-const-nothing`)",
  "reward 0; matches 0 of 82 hand and 0 of 330 small generated files"),
 ("positional: the conditions in query order over whole columns (`cheat-pos-query-order`)",
  "reward 0; matches 72 of 82 hand files (mostly those with one condition, where query order is the order) and 11 of 330 small generated files"),
 ("the worked example's output replayed for every file (`cheat-replay-example`)",
  "reward 0; matches 0 of 82 and 0 of 330, since tiny.txt is not graded"),
 ("the frozen answers for the enumerated set carried in a collected file, keyed on each file's query history (`cheat-forge-hand`)",
  "reward 0; matches all 82 hand files and 0 of the 330 small generated files it could not have seen"),
 ("the previous design of this engine, the one three local agents solved (`cheat-previous-design`)",
  "reward 0; matches 45 of 82 hand files and 117 of 330 small generated files"),
]

TOLERANCES = [
 ("`tests/test.sh:38` the 60 second clock on the graded run",
  "`authoring/scan-chunk-pick/variants/ok-slice` (settlement kept per row, no maintained counts, version-stamped heap) "
  "and `authoring/scan-chunk-pick/variants/ok-tree` (segment tree of exact minima, maintained live counts, chunk counts summed afresh from pages), both written apart from the reference",
  "whole 418-file graded set in a python:3.12-slim container at 1 CPU and 2 GB: reference 7.1 s, ok-slice 9.7 s, ok-tree 9.7 s, "
  "against 60 s. The naive family the limit rules out is the rescan loop (`cheat-slow-rescan`): 139.6 s on one wide file on "
  "the host against 1.6 s for the reference, with a trace identical to the reference's."),
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
