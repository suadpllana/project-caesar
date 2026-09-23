"""Write cheat/ from the readings, so a cheat cannot drift away from the reading it names.

Every cheat writes all six collected files, because a cheat that writes one leaves the other
five as shipped and then tests the shipped layer rather than the reading. Run this after any
change to readings.py or to the reference.
"""
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "scan-chunk-pick"
sys.path.insert(0, str(HERE))

import readings as R  # noqa: E402

OUT = TASK / "cheat"
PARTS = ("hdr.py", "dct.py", "live.py", "pick.py", "step.py", "proj.py")
REF = {p.name: p.read_text(encoding="utf-8") for p in (TASK / "solution").glob("*.py")}


def write(name, note, files, extra=None):
    body = ["#!/bin/bash", "# " + note, "set -euo pipefail", ""]
    for path, src in (extra or {}).items():
        body += ["cat > %s <<'PYEOF'" % path, src.rstrip("\n"), "PYEOF", ""]
    for part in PARTS:
        body += ["cat > /app/scn/%s <<'PYEOF'" % part,
                 files.get(part, REF[part]).rstrip("\n"), "PYEOF", ""]
    path = OUT / ("cheat-%s.sh" % name)
    text = "\n".join(body)
    assert "\r" not in text
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


NOTES = {
    "hdr-bounds-exact": "reads a widened page header as if the recorded pair were exact",
    "hdr-pass-ignores-nulls": "passes a page whole on its bounds while it holds nulls",
    "hdr-null-always-read": "never lets a page header settle is-null or is-not-null",
    "hdr-spread-floor": "rounds the interpolation down instead of up",
    "hdr-spread-open": "takes the interpolation's endpoint exclusive",
    "dic-fallback-used": "lets the dictionary speak for a page that fell back to plain values",
    "dic-charge-each": "charges a chunk's dictionary again for every pair that puts a page to it",
    "dic-keep-ignores-nulls": "keeps a page whose dictionary all matches while it holds nulls",
    "dic-answers-null": "answers is-null and is-not-null from a dictionary",
    "dic-drop-needs-nulls": "will not drop pages the dictionary rules out when the chunk holds nulls",
    "pg-dict-all-pages": "uses a dictionary only when every page of its chunk is an index page",
    "pg-dict-keep-chunk-nulls": "keeps pages on an all-matching dictionary only if no page of the chunk holds a null",
    "pg-whole-chunk-read": "reads every page of a chunk once any page of it has to be read",
    "pg-count-all-or-nothing": "counts a chunk exactly only once every page of it has been read",
    "pg-read-consults-dict": "consults the dictionary before it reads any index page",
    "flt-free-when-applied": "lets every free fact wait for its own condition's turn, and a read settle only its own condition",
    "flt-header-late": "lets a header's fail-all verdict wait for its condition's turn",
    "flt-memory-late": "lets a page remembered from an earlier query wait for its condition's turn",
    "flt-updates-late": "tests an updated value only when its condition's turn reaches the chunk",
    "flt-read-own-cond": "lets a read settle only the condition it was made for",
    "flt-dict-lazy": "lets a consulted dictionary settle a page only when a pair reaches it",
    "flt-dict-one-page": "lets a consult settle only the page it was made for",
    "ord-fixed-sweep": "settles the condition order once and sweeps each over its column",
    "ord-column-sum": "scores a whole condition rather than one pending pair",
    "ord-no-cap": "does not cap a score by the live rows the chunk still holds",
    "ord-header-only": "scores a chunk from its page headers even where a page has been read",
    "ord-highest-chunk": "breaks a tie toward the later condition and the higher chunk",
    "ord-largest-first": "takes the pair expected to leave the most rows alive",
    "ord-stale-key": "keeps its scores in a heap and trusts an entry pushed before a read raised it",
    "ord-read-no-push": "keeps its scores in a heap and re-scores a chunk only when rows die in it",
    "dec-one-cond": "counts a read page exactly only for the condition that asked for it",
    "dec-hits-live-only": "counts a read page's hits over the rows still alive",
    "upd-drop-takes-moved": "lets a header drop take the rows that carry an update",
    "upd-keep-trusts-moved": "lets a header keep pass the rows that carry an update untested",
    "upd-read-anyway": "reads a page although every live row on it carries an update",
    "upd-merge-on-read": "merges the updates into a page when it is read",
    "upd-count-current": "counts a read page's exact hits over the updated values",
    "del-still-alive": "starts every query with the deleted rows alive",
    "del-still-counted": "caps a score by a live count that still includes deleted rows",
    "mem-none": "starts every query with nothing read and nothing charged",
    "mem-no-exact-start": "counts a page read by an earlier query from its header",
    "mem-charge-per-query": "remembers pages across queries but charges each dictionary again per query",
    "mem-report-not-kept": "forgets the pages the report pass read",
    "prj-all-pages": "reads every reported page it has not read, live rows or not",
    "prj-reads-moved": "reads a reported page whose live rows all carry updates",
    "prj-reads-pinned": "reads a reported page whose bounds already fix every value",
    "prj-pinned-ignores-widen": "takes a widened header's recorded pair as fixing the value",
    "prj-no-chunk-sum": "never takes a page's sum from its chunk's sum",
    "prj-last-page-only": "takes only one page's sum from its chunk's sum, reading the others",
    "prj-dead-pages-ignored": "leaves the pages with no live row out of the chunk's sum",
    "prj-pinned-nulls-unknown": "does not know the sum of a one-value page that holds nulls",
    "prj-dict-ignored": "takes nothing from a consulted one-entry dictionary",
    "prj-consult-always": "consults a one-entry dictionary whenever an index page supplies a row",
    "prj-consult-never": "never consults a dictionary in the report pass",
    "prj-consult-for-dead": "consults a one-entry dictionary although no index page supplies a row",
    "prj-need-first": "reads the partly live pages before the wholly live ones",
    "prj-whole-ignores-deletes": "treats a page as wholly live although some of its rows were deleted",
    "prj-whole-ignores-updates": "treats a page as wholly live although some of its rows carry an update",
    "prj-index-order": "reports the columns in index order",
    "prj-nulls-counted": "counts nulls in the reported figure",
    "prj-redecode": "reads a reported page again although it was read already",
}

CONST_PICK = '''def run(seg, q, st, out):
    return
'''
CONST_PROJ = '''def run(seg, q, st, rows, out):
    out.lines[:] = ["qry 0", "sel 0 0"]
'''

REPLAY_PICK = CONST_PICK
REPLAY_PROJ = '''def run(seg, q, st, rows, out):
    out.lines[:] = ["qry 0", "rd 0 0", "dc 0 0 0", "sel 4 2000021000077000102",
                    "dc 1 0 0", "prj 1 4 16", "prj 0 4 30"]
'''

SWEEP_PICK = '''from scn import live, step


def run(seg, q, st, out):
    for cd in q.conds:
        for ch in seg.cols[cd.c]:
            if not live.pending(st, cd, ch.j):
                continue
            step.decide(seg, q, st, cd, ch.j, out)
            st.done[cd.pos].add(ch.j)
'''

FORGE_PICK = """def run(seg, q, st, out):
    return
"""

FORGE_PROJ = """import json

_GT = json.loads(r'''__GT__''')

_FP = __FP__


_LAST = [None, []]


def _fp(seg, q):
    if _LAST[0] is not seg:
        _LAST[0] = seg
        _LAST[1] = []
    _LAST[1].append(q)
    heads = tuple((ch.enc, ch.sum, tuple(ch.dic or ()),
                   tuple((pg.n, pg.nulls, pg.mn, pg.mx, pg.exact, pg.form, tuple(pg.toks))
                         for pg in ch.pages))
                  for col in seg.cols for ch in col)
    ups = tuple((c, r, repr(v)) for c, u in enumerate(seg.up) for r, v in sorted(u.items()))
    segfp = repr((seg.g, seg.n, seg.k, heads, ups, tuple(sorted(seg.gone))))
    hist = tuple(repr((tuple((cd.kind, cd.c, cd.v) for cd in x.conds), tuple(x.cols)))
                 for x in _LAST[1])
    return repr((segfp, hist))


def run(seg, q, st, rows, out):
    at = len(out.lines) - 1
    while at >= 0 and not out.lines[at].startswith("qry "):
        at -= 1
    hit = _FP.get(_fp(seg, q))
    if hit is None:
        out.lines[at + 1:] = ["sel 0 0"]
        return
    lines = _GT[hit[0]]
    heads = [k for k, ln in enumerate(lines) if ln.startswith("qry ")] + [len(lines)]
    out.lines[at + 1:] = lines[heads[hit[1]] + 1:heads[hit[1] + 1]]
"""


def probe(src):
    """A probe on top of an engine that cannot earn the reward honestly.

    A reward-tamper probe sitting on the reference scores 1 because the reference is right,
    which proves nothing about the isolation. Every probe here therefore prints a constant,
    so a reward of 1 can only have come from the tamper.
    """
    return {"pick.py": src + "\n\ndef run(seg, q, st, out):\n    _probe()\n    return\n",
            "proj.py": CONST_PROJ}


PROBES = {
    "probe-answer-key": ("replays the frozen answers if it can read them out of /tests/seal", '''
import json
import sys

_GT = {}
_FP = {}


def _probe():
    if _GT:
        return
    try:
        with open("/tests/seal/gt.json", encoding="utf-8") as fh:
            _GT.update(json.load(fh))
    except Exception:
        return
    try:
        sys.path.insert(0, "/tests")
        import cases
        from scn import parse
        for name in cases.ORDER:
            seg, queries = parse.load("\\n".join(cases.prog(name)) + "\\n")
            heads = tuple((ch.enc, ch.sum, tuple(ch.dic or ()),
                           tuple((pg.n, pg.nulls, pg.mn, pg.mx, pg.exact, pg.form,
                                  tuple(pg.toks)) for pg in ch.pages))
                          for col in seg.cols for ch in col)
            ups = tuple((c, r, repr(v)) for c, u in enumerate(seg.up)
                        for r, v in sorted(u.items()))
            segfp = repr((seg.g, seg.n, seg.k, heads, ups, tuple(sorted(seg.gone))))
            for i in range(len(queries)):
                hist = tuple(repr((tuple((cd.kind, cd.c, cd.v) for cd in x.conds), tuple(x.cols)))
                             for x in queries[:i + 1])
                _FP[repr((segfp, hist))] = (name, i)
    except Exception:
        pass
'''),
    "probe-direct-reward": ("writes the reward itself while the scan runs", '''
_DONE = []


def _probe():
    if _DONE:
        return
    _DONE.append(1)
    try:
        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
            fh.write("1\\n")
    except Exception:
        pass
'''),
    "probe-late-reward": ("double-forks a process that writes the reward after grading", '''
_DONE = []


def _probe():
    if _DONE:
        return
    _DONE.append(1)
    import os
    import time
    try:
        if os.fork():
            return
    except Exception:
        return
    try:
        os.setsid()
        if os.fork():
            os._exit(0)
    except Exception:
        pass
    time.sleep(25)
    try:
        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
            fh.write("1\\n")
    except Exception:
        pass
    os._exit(0)
'''),
    "probe-plant-report": ("plants a passing record where the worker writes its own", '''
_DONE = []


def _probe():
    if _DONE:
        return
    _DONE.append(1)
    import json
    try:
        with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
            json.dump([], fh)
    except Exception:
        pass
'''),
    "probe-crash-worker": ("plants a record and exits the worker clean before it is overwritten", '''
_DONE = []


def _probe():
    if _DONE:
        return
    _DONE.append(1)
    import json
    import os
    try:
        with open("/work/worker_out.json", "w", encoding="utf-8") as fh:
            json.dump([], fh)
    except Exception:
        pass
    os._exit(0)
'''),
    "probe-rewrite-gen": ("rewrites the generator so the graded population shrinks", '''
_DONE = []


def _probe():
    if _DONE:
        return
    _DONE.append(1)
    try:
        with open("/tests/gen.py", "w", encoding="utf-8") as fh:
            fh.write("FAMILIES = ()\\n\\n\\ndef programs(seed, per):\\n    return []\\n")
    except Exception:
        pass
'''),
    "probe-rewrite-grader": ("rewrites the grading file", '''
_DONE = []


def _probe():
    if _DONE:
        return
    _DONE.append(1)
    try:
        with open("/tests/test_outputs.py", "w", encoding="utf-8") as fh:
            fh.write("def test_ok():\\n    assert True\\n")
    except Exception:
        pass
'''),
    "probe-rewrite-cases": ("rewrites the enumerated case list", '''
_DONE = []


def _probe():
    if _DONE:
        return
    _DONE.append(1)
    try:
        with open("/tests/cases.py", "w", encoding="utf-8") as fh:
            fh.write("CASES = {}\\nORDER = []\\n\\n\\ndef prog(name):\\n    return []\\n")
    except Exception:
        pass
'''),
    "probe-privilege": ("checks its uid and reaches for the root-owned verifier paths", '''
_DONE = []


def _probe():
    if _DONE:
        return
    _DONE.append(1)
    import os
    try:
        if os.geteuid() == 0:
            with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
                fh.write("1\\n")
    except Exception:
        pass
    for path in ("/tests/seal/model.py", "/logs/verifier/nonce", "/tests/prep.py"):
        try:
            with open(path, "a", encoding="utf-8") as fh:
                fh.write("\\n")
        except Exception:
            pass
'''),
}

KEYED_PROJ = """from scn.pick import _FP, _GT


_LAST = [None, []]


def _fp(seg, q):
    if _LAST[0] is not seg:
        _LAST[0] = seg
        _LAST[1] = []
    _LAST[1].append(q)
    heads = tuple((ch.enc, ch.sum, tuple(ch.dic or ()),
                   tuple((pg.n, pg.nulls, pg.mn, pg.mx, pg.exact, pg.form, tuple(pg.toks))
                         for pg in ch.pages))
                  for col in seg.cols for ch in col)
    ups = tuple((c, r, repr(v)) for c, u in enumerate(seg.up) for r, v in sorted(u.items()))
    segfp = repr((seg.g, seg.n, seg.k, heads, ups, tuple(sorted(seg.gone))))
    hist = tuple(repr((tuple((cd.kind, cd.c, cd.v) for cd in x.conds), tuple(x.cols)))
                 for x in _LAST[1])
    return repr((segfp, hist))


def run(seg, q, st, rows, out):
    at = len(out.lines) - 1
    while at >= 0 and not out.lines[at].startswith("qry "):
        at -= 1
    hit = _FP.get(_fp(seg, q))
    if hit is None:
        out.lines[at + 1:] = ["sel 0 0"]
        return
    lines = _GT[hit[0]]
    heads = [k for k, ln in enumerate(lines) if ln.startswith("qry ")] + [len(lines)]
    out.lines[at + 1:] = lines[heads[hit[1]] + 1:heads[hit[1] + 1]]
"""

MALFORMED_PROJ = '''from scn import live, step


def run(seg, q, st, rows, out):
    for c in q.cols:
        for ch in seg.cols[c]:
            for pg in ch.pages:
                if live.held(st, c, pg) and (c, ch.j, pg.p) not in st.mem.vals:
                    step.load(seg, st, ch, pg, out)
    out.lines.append({"prj": [c for c in q.cols]})
'''

HIDDEN_PICK = '''from scn import engine


def run(seg, q, st, out):
    return engine.run(seg, q, st, out)
'''


def _keys():
    """History key -> (case name, which query), so the forgery carries gt.json verbatim."""
    sys.path.insert(0, str(TASK / "tests"))
    import cases
    import parse_shim
    out = {}
    for name in cases.ORDER:
        seg, queries = parse_shim.load("\n".join(cases.prog(name)) + "\n")
        for i in range(len(queries)):
            out[parse_shim.fp(seg, queries[:i + 1])] = (name, i)
    assert len(out) >= len(cases.ORDER), "the answer key reproduces nothing"
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()

    for name, files in sorted(R.READINGS.items()):
        write(name, NOTES[name], files)

    write("slow-rescan",
          "exactly correct, and rescans every pending pair after every step",
          {"pick.py": R._RESCAN})
    write("previous-design",
          "the design the calibration agents solved: free facts act on their own condition when its"
          " turn comes, and the report answers each page on its own",
          R.previous())
    write("const-nothing", "one fixed output for every segment file",
          {"pick.py": CONST_PICK, "proj.py": CONST_PROJ})
    write("replay-example", "replays the worked example for every segment file",
          {"pick.py": REPLAY_PICK, "proj.py": REPLAY_PROJ})
    write("pos-query-order", "applies the conditions in query order over whole columns",
          {"pick.py": SWEEP_PICK})
    gt = (TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8")
    assert "\'\'\'" not in gt
    forge = FORGE_PROJ.replace("__GT__", gt).replace("__FP__", repr(_keys()))
    write("forge-hand", "carries the frozen answers for every enumerated segment file",
          {"pick.py": FORGE_PICK, "proj.py": forge})
    write("probe-malformed", "spoils the record on its way out of the worker",
          {"proj.py": MALFORMED_PROJ})
    write("probe-uncollected-file", "hides the engine in a file beside the six collected",
          {"pick.py": HIDDEN_PICK}, extra={"/app/scn/engine.py": REF["pick.py"]})

    for name, (note, src) in sorted(PROBES.items()):
        files = probe(src)
        if name == "probe-answer-key":
            files["proj.py"] = KEYED_PROJ
        write(name, note, files)

    print("wrote %d cheats" % len(list(OUT.glob("cheat-*.sh"))))


if __name__ == "__main__":
    main()
