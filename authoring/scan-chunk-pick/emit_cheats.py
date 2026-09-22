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
    "hdr-bounds-exact": "reads a widened header as if the recorded pair were exact",
    "hdr-pass-ignores-nulls": "keeps a chunk unread on its bounds while it holds nulls",
    "hdr-null-always-read": "never lets the header settle is-null or is-not-null",
    "hdr-spread-floor": "rounds the interpolation down instead of up",
    "hdr-spread-open": "takes the interpolation's endpoint exclusive",
    "dic-overflow-used": "uses a dictionary that falls back to a literal",
    "dic-charge-each": "charges a chunk's dictionary once per consult",
    "dic-keep-ignores-nulls": "keeps a chunk whose dictionary all matches while it holds nulls",
    "dic-answers-null": "answers is-null and is-not-null from a dictionary",
    "dic-drop-needs-nulls": "will not drop a ruled-out chunk that holds nulls",
    "ord-fixed-sweep": "settles the condition order once and sweeps each over its column",
    "ord-column-sum": "scores a whole condition rather than one pending pair",
    "ord-no-cap": "does not cap a score by the survivors the chunk still holds",
    "ord-header-only": "scores a chunk that has been read from its header",
    "ord-highest-chunk": "breaks a tie toward the later condition and the higher chunk",
    "ord-largest-first": "takes the pair expected to leave the most rows alive",
    "dec-one-cond": "records only the condition that asked for the read",
    "dec-hits-live-only": "counts a read chunk's hits over the rows still alive",
    "prj-all-chunks": "reads every chunk of a reported column",
    "prj-index-order": "reports the columns in index order",
    "prj-nulls-counted": "counts nulls in the reported figure",
    "prj-redecode": "reads a reported chunk again although it was read already",
    "qry-keeps-state": "carries reads and dictionary charges from one query into the next",
}

SLOW_LIVE = '''from scn import rd


class State:
    __slots__ = ("seg", "alive", "own", "vals", "hit", "dread", "done")


def _cols(q):
    seen = []
    for cd in q.conds:
        if cd.c not in seen:
            seen.append(cd.c)
    for c in q.cols:
        if c not in seen:
            seen.append(c)
    return seen


def start(seg, q):
    st = State()
    st.seg = seg
    st.alive = set(range(seg.n))
    st.own = {}
    st.vals = {}
    st.hit = {}
    st.dread = set()
    st.done = [set() for _ in q.conds]
    for c in _cols(q):
        own = []
        for ch in seg.cols[c]:
            own.extend([ch.j] * ch.n)
        st.own[c] = own
    return st


def count(st, c, j):
    ch = st.seg.cols[c][j]
    lo = ch.start
    hi = lo + ch.n
    t = 0
    for r in st.alive:
        if lo <= r < hi:
            t += 1
    return t


def kill(st, dead):
    st.alive.difference_update(dead)


def drop_chunk(st, c, j):
    ch = st.seg.cols[c][j]
    kill(st, range(ch.start, ch.start + ch.n))


def filter_chunk(st, c, j, cond, vals):
    ch = st.seg.cols[c][j]
    s = ch.start
    kill(st, [s + i for i in range(ch.n) if not rd.sat(cond, vals[i])])


def rows(st):
    return sorted(st.alive)
'''

CONST_PICK = '''def run(seg, q, st, out):
    return
'''
CONST_PROJ = '''def run(seg, q, st, rows, out):
    out.lines[:] = ["qry 0", "sel 0 0"]
'''

REPLAY_PICK = CONST_PICK
REPLAY_PROJ = '''def run(seg, q, st, rows, out):
    out.lines[:] = ["qry 0", "rd 0 0", "dc 0 0", "sel 4 2000021000077000102",
                    "dc 1 0", "prj 1 4 16", "prj 0 4 30"]
'''

SWEEP_PICK = '''from scn import live, step


def run(seg, q, st, out):
    for cd in q.conds:
        for ch in seg.cols[cd.c]:
            if live.count(st, cd.c, ch.j) <= 0:
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


def _fp(seg, q):
    heads = tuple((ch.n, ch.nulls, ch.mn, ch.mx, ch.exact, ch.enc)
                  for col in seg.cols for ch in col)
    return repr((seg.g, seg.n, seg.k, heads,
                 tuple((cd.kind, cd.c, cd.v) for cd in q.conds), tuple(q.cols)))


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
            for i, q in enumerate(queries):
                heads = tuple((ch.n, ch.nulls, ch.mn, ch.mx, ch.exact, ch.enc)
                              for col in seg.cols for ch in col)
                key = repr((seg.g, seg.n, seg.k, heads,
                            tuple((cd.kind, cd.c, cd.v) for cd in q.conds), tuple(q.cols)))
                _FP[key] = (name, i)
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


def _fp(seg, q):
    heads = tuple((ch.n, ch.nulls, ch.mn, ch.mx, ch.exact, ch.enc)
                  for col in seg.cols for ch in col)
    return repr((seg.g, seg.n, seg.k, heads,
                 tuple((cd.kind, cd.c, cd.v) for cd in q.conds), tuple(q.cols)))


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
            if live.count(st, c, ch.j) > 0 and (c, ch.j) not in st.vals:
                step.load(seg, q, st, ch, out)
    out.lines.append({"prj": [c for c in q.cols]})
'''

HIDDEN_PICK = '''from scn import engine


def run(seg, q, st, out):
    return engine.run(seg, q, st, out)
'''


def _keys():
    """Fingerprint -> (case name, which query), so the forgery carries gt.json verbatim."""
    sys.path.insert(0, str(TASK / "tests"))
    import cases
    import parse_shim
    out = {}
    for name in cases.ORDER:
        seg, queries = parse_shim.load("\n".join(cases.prog(name)) + "\n")
        for i, q in enumerate(queries):
            out[parse_shim.fp(seg, q)] = (name, i)
    assert len(out) >= len(cases.ORDER), "the answer key reproduces nothing"
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()

    for name, files in sorted(R.READINGS.items()):
        write(name, NOTES[name], files)

    write("slow-rowid-set",
          "exactly correct, and holds the survivors as row ids every score walks", 
          {"live.py": SLOW_LIVE})
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
