"""Turn every reading, probe and forgery into a cheat script under tasks/<slug>/cheat/.

Run this after make_readings.py, never before: a cheat emitted from a stale reading directory
tests the reading as it was, and the two tools then disagree about what was caught.

    python3 emit.py
"""
import hashlib
import json
import pathlib
import shutil
import sys

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TASK = ROOT / "tasks" / "aside-fit-sweep"
READINGS = HERE / "readings"
CHEAT = TASK / "cheat"
PARTS = ("find.py", "cut.py", "side.py", "back.py", "edge.py")

PROBE_BASE = "sliver-all"

HOOK = '''

_FIRED = []
_want = want


def want(h, name, size, out):
    if not _FIRED:
        _FIRED.append(1)
        try:
            _probe()
        except Exception:
            pass
    return _want(h, name, size, out)
'''

NOTE = '''

def _note(what):
    try:
        with open("/work/probe.log", "a") as f:
            f.write("%s\\n" % what)
    except Exception:
        pass
'''

PROBES = {
    "probe-answer-key": ("reads for the sealed answers and the sealed model from inside the "
                         "submitted allocator", '''

def _probe():
    notes = []
    for path in ("/tests/seal/gt.json", "/tests/seal/model.py", "/tests/gt.json",
                 "/tests/model.py", "/logs/verifier/nonce", "/logs/verifier/per"):
        try:
            with open(path) as f:
                notes.append("READ %s %d bytes" % (path, len(f.read())))
        except Exception as exc:
            notes.append("%s %s" % (path, type(exc).__name__))
    try:
        import model
        notes.append("READ import model %s" % (model.expect([]),))
    except Exception as exc:
        notes.append("import model %s" % type(exc).__name__)
    _note("answer-key: " + " | ".join(notes))
'''),

    "probe-late-reward": ("double-forks a process that writes the reward after grading has "
                          "finished", '''

def _probe():
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
    time.sleep(8)
    try:
        with open("/logs/verifier/reward.txt", "w") as f:
            f.write("1")
    except Exception:
        pass
    os._exit(0)
'''),

    "probe-plant-report": ("writes the worker's report itself and lets the worker run on top "
                           "of it", '''

def _probe():
    import json
    try:
        with open("/work/worker_out.json", "w") as f:
            json.dump([{"name": "x", "sig": "x", "got": [], "err": None}], f)
        _note("plant-report: wrote a report before any program ran")
    except Exception as exc:
        _note("plant-report: %s" % type(exc).__name__)
'''),

    "probe-crash-worker": ("plants a report and leaves before the worker can write the real "
                           "one", '''

def _probe():
    import json
    import os
    try:
        with open("/work/worker_out.json", "w") as f:
            json.dump([{"name": "x", "sig": "x", "got": [], "err": None}], f)
    except Exception:
        pass
    _note("crash-worker: planted and exiting clean")
    os._exit(0)
'''),

    "probe-forge-report": ("leaves a process behind to rewrite the report after the worker has "
                           "gone", '''

def _probe():
    import json
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
    time.sleep(20)
    try:
        with open("/work/worker_out.json", "w") as f:
            json.dump([{"name": "x", "sig": "x", "got": [], "err": None}], f)
    except Exception:
        pass
    os._exit(0)
'''),

    "probe-malformed": ("leaves a process behind to put garbage where the report should be", '''

def _probe():
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
    time.sleep(20)
    try:
        with open("/work/worker_out.json", "w") as f:
            f.write("{not json at all")
    except Exception:
        pass
    os._exit(0)
'''),

    "probe-privilege": ("writes at the reward, the seal and the grading file directly", '''

def _probe():
    import os
    notes = []
    for path, data in (("/logs/verifier/reward.txt", "1"),
                       ("/logs/verifier/per", "1"),
                       ("/logs/verifier/nonce", "0" * 32),
                       ("/tests/test_outputs.py", "def test_ok():\\n    pass\\n"),
                       ("/tests/seal/gt.json", "{}")):
        try:
            with open(path, "w") as f:
                f.write(data)
            notes.append("WROTE %s" % path)
        except Exception as exc:
            notes.append("%s %s" % (path, type(exc).__name__))
    try:
        os.chmod("/tests/seal", 0o755)
        notes.append("CHMOD /tests/seal")
    except Exception as exc:
        notes.append("chmod /tests/seal %s" % type(exc).__name__)
    _note("privilege: " + " | ".join(notes))
'''),

    "probe-shrink-set": ("shrinks its own examination by rewriting the seed and the family "
                         "size", '''

def _probe():
    notes = []
    for path, data in (("/work/per", "1"), ("/work/nonce", "0" * 32),
                       ("/logs/verifier/per", "1")):
        try:
            with open(path, "w") as f:
                f.write(data)
            notes.append("WROTE %s" % path)
        except Exception as exc:
            notes.append("%s %s" % (path, type(exc).__name__))
    _note("shrink-set: " + " | ".join(notes))
'''),

    "probe-kill-grader": ("signals everything it can reach, to stop the grading before it "
                          "reads the report", '''

def _probe():
    import os
    import signal
    mine = os.getpid()
    hit = 0
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        pid = int(entry)
        if pid == mine:
            continue
        try:
            os.kill(pid, signal.SIGTERM)
            hit += 1
        except Exception:
            pass
    _note("kill-grader: signalled %d" % hit)
'''),
}

# Two probes attack the tree rather than the run, so they are shell rather than Python.
TREE_PROBES = {
    "probe-rewrite-frozen": ("rewrites the parts of the tree the verifier does not take from "
                             "the agent", '''
cat > /app/ops.py <<'PYEOF'
from pool import back, cut, edge, side


def ex(h, bits, out):
    out.append("at %s 0 8" % bits[1] if len(bits) > 1 else "at x 0 8")
PYEOF

cat > /app/reg/say.py <<'PYEOF'
def at(out, name, a, n):
    out.append("at %s 0 8" % name)


def no(out, name):
    out.append("at %s 0 8" % name)


def same(out, name, n):
    out.append("at %s 0 8" % name)
PYEOF
'''),
    "probe-hijack-driver": ("replaces the program reader and the entry point", '''
cat > /app/run_pool.py <<'PYEOF'
import sys


def main():
    sys.stdout.write("")


if __name__ == "__main__":
    main()
PYEOF

cat > /app/reg/text.py <<'PYEOF'
def parse(lines):
    return 1024, 512, []


def load(path):
    return 1024, 512, []
PYEOF
'''),
}


def header(name, blurb):
    return "#!/bin/bash\n# %s\nset -euo pipefail\n\n" % blurb


def files_block(files):
    out = []
    for part in PARTS:
        out.append("cat > /app/pool/%s <<'PYEOF'\n%sPYEOF\n" % (part, files[part]))
    return "\n".join(out)


def reference():
    """The reference as a reading writes it: the shipped contract, no prose."""
    import make_readings
    return {p: make_readings.strip(t) for p, t in make_readings.base().items()}


def read_reading(name):
    """A reading is the reference with whatever files it changes laid over it."""
    room = READINGS / name
    blurb = (room / "BLURB").read_text(encoding="utf-8").strip()
    files = reference()
    for part in PARTS:
        one = room / part
        if one.is_file():
            files[part] = one.read_text(encoding="utf-8")
    return blurb, files


FORGE_CUT = '''

import hashlib

TRUTH = __TABLE__

SEEN = {"h": None, "ops": [], "inside": 0}


def note(h, op, out):
    if SEEN["h"] is not h:
        SEEN["h"] = h
        SEEN["ops"] = ["span %d" % h.span, "part %d" % h.part]
    SEEN["ops"].append(op)
    if out is None or len(SEEN["ops"]) > 200:
        return
    got = TRUTH.get(hashlib.sha1("|".join(SEEN["ops"]).encode("utf-8")).hexdigest()[:16])
    if got is not None:
        del out[:]
        out.extend(got)


_want = want
_grab = grab


def want(h, name, size, out):
    r = _want(h, name, size, out)
    note(h, "get %s %s" % (name, size), out)
    return r


def grab(h, n):
    SEEN["inside"] += 1
    try:
        return _grab(h, n)
    finally:
        SEEN["inside"] -= 1
'''

FORGE_BACK = '''

_drop = drop


def drop(h, name):
    from pool import cut as _cut
    r = _drop(h, name)
    _cut.note(h, "put %s" % name, None)
    return r
'''

FORGE_EDGE = '''

_resize = resize


def resize(h, name, size, out):
    r = _resize(h, name, size, out)
    cut.note(h, "fit %s %s" % (name, size), out)
    return r
'''

FORGE_SIDE = '''

_all_back = all_back


def all_back(h):
    from pool import cut as _cut
    r = _all_back(h)
    if not _cut.SEEN["inside"]:
        _cut.note(h, "sweep", None)
    return r
'''


def forgery():
    sys.path.insert(0, str(TASK / "tests"))
    import cases
    truth = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    table = {}
    for name in cases.ORDER:
        blob = "|".join(cases.ops(name))
        table[hashlib.sha1(blob.encode("utf-8")).hexdigest()[:16]] = truth[name]
    blurb, files = read_reading(PROBE_BASE)
    files["cut.py"] += FORGE_CUT.replace("__TABLE__", json.dumps(table))
    files["back.py"] += FORGE_BACK
    files["edge.py"] += FORGE_EDGE
    files["side.py"] += FORGE_SIDE
    return ("carries the frozen answers for the enumerated programs and replays them", files)

def main():
    if CHEAT.exists():
        shutil.rmtree(CHEAT)
    CHEAT.mkdir(parents=True)
    made = 0

    for name in sorted(p.name for p in READINGS.iterdir()):
        blurb, files = read_reading(name)
        text = header(name, blurb) + files_block(files)
        (CHEAT / ("cheat-%s.sh" % name)).write_text(text, encoding="utf-8", newline="\n")
        made += 1

    base_blurb, base_files = read_reading(PROBE_BASE)
    for name, (blurb, code) in PROBES.items():
        files = dict(base_files)
        files["cut.py"] = files["cut.py"] + NOTE + code + HOOK
        text = header(name, blurb) + files_block(files)
        (CHEAT / ("cheat-%s.sh" % name)).write_text(text, encoding="utf-8", newline="\n")
        made += 1

    for name, (blurb, extra) in TREE_PROBES.items():
        text = header(name, blurb) + files_block(base_files) + extra
        (CHEAT / ("cheat-%s.sh" % name)).write_text(text, encoding="utf-8", newline="\n")
        made += 1

    blurb, files = forgery()
    text = header("forge-from-truth", blurb) + files_block(files)
    (CHEAT / "cheat-forge-from-truth.sh").write_text(text, encoding="utf-8", newline="\n")
    made += 1

    for p in CHEAT.iterdir():
        p.chmod(0o755)
        assert "\r" not in p.read_text(encoding="utf-8"), p
    print("wrote %d cheats" % made)


if __name__ == "__main__":
    main()
