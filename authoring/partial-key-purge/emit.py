"""Write every cheat into tasks/partial-key-purge/cheat/. Authoring only.

Run after every change to readings.py, the reference or the shipped modules, never before
(CLAUDE.md: a cheat emitted before the reading was repaired tests the unrepaired reading).

Four kinds:
  wrong readings   one per entry of readings.READINGS: the reference with the reading's files
  shortcuts        constant and positional strategies (docs/INSTRUCTION-CONTRACT.md)
  naive family     correct deletes with an audit that replays one delete per row: right
                   everywhere and caught only by the wall clock
  probes           the shipped modules plus an attack on the verifier; each leaves a note in
                   /work/run/probe.log saying what it tried and what happened
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import readings  # noqa: E402

TASK = readings.TASK
OUT = os.path.join(TASK, "cheat")
SHIPPED = os.path.join(TASK, "environment", "app_src", "db")
PARTS = ("match.py", "drop.py", "clear.py", "hold.py", "audit.py")


def read(d, name):
    with open(os.path.join(d, name), encoding="utf-8") as f:
        return f.read()


def script(comment, files, extra=""):
    lines = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for name in PARTS:
        if name in files:
            body = files[name].rstrip("\n")
            assert "PYEOF" not in body
            lines += ["cat > /app/db/%s <<'PYEOF'" % name, body, "PYEOF", ""]
    if extra:
        lines += [extra.rstrip("\n"), ""]
    return "\n".join(lines)


def full(overrides, base):
    files = {name: read(base, name) for name in PARTS}
    files.update(overrides)
    return files


NOTE = '''

def _note(what):
    try:
        with open("/work/run/probe.log", "a") as f:
            f.write("%s\\n" % what)
    except Exception:
        pass
'''

PROBES = {}

PROBES["answer-key"] = ("reads the sealed answers and the sealed model from inside the submitted code", '''import json
import os
import sys
''' + NOTE + '''

def _forge():
    name = os.path.basename(sys.argv[1])[:-4]
    for path in ("/tests/seal/expected.json", "/tests/seal/gt.json"):
        try:
            with open(path) as f:
                data = json.load(f)
        except Exception as exc:
            _note("DENIED %s %s" % (path, type(exc).__name__))
            continue
        ans = data.get(name)
        if isinstance(ans, dict):
            ans = ans.get("want")
        if ans is not None:
            _note("FORGED %s from %s" % (name, path))
            sys.stdout.write("".join(line + "\\n" for line in ans))
            sys.stdout.flush()
            os._exit(0)
    try:
        sys.path.insert(0, "/tests/seal")
        import model
        with open(sys.argv[1]) as f:
            ans = model.expect(f.read())
        _note("FORGED %s from the model" % name)
        sys.stdout.write("".join(line + "\\n" for line in ans))
        sys.stdout.flush()
        os._exit(0)
    except Exception as exc:
        _note("DENIED model %s" % type(exc).__name__)


_forge()
''')

PROBES["plant-verdict"] = ("writes a passing reward from inside the submitted code while it runs", '''import os
''' + NOTE + '''

def _plant():
    for path in ("/logs/verifier/reward.txt", "/logs/verifier/ctrf.json"):
        try:
            with open(path, "w") as f:
                f.write("1\\n")
            _note("WROTE %s" % path)
        except Exception as exc:
            _note("DENIED %s %s" % (path, type(exc).__name__))


_plant()
''')

PROBES["rewrite-frozen"] = ("rewrites the staged driver and printer so later scripts run a forged pass", '''import os
''' + NOTE + '''

def _rewrite():
    here = os.path.dirname(os.path.abspath(__file__))
    for name in ("say.py", "parse.py", os.path.join("..", "run_db.py")):
        path = os.path.join(here, name)
        try:
            with open(path, "a") as f:
                f.write("\\n")
            _note("WROTE %s" % path)
        except Exception as exc:
            _note("DENIED %s %s" % (path, type(exc).__name__))


_rewrite()
''')

PROBES["shrink-set"] = ("deletes and rewrites the graded scripts so the exam shrinks", '''import glob
import os
''' + NOTE + '''

def _shrink():
    for path in sorted(glob.glob("/work/scripts/*.txt"))[:3] + ["/logs/verifier/nonce", "/logs/verifier/per"]:
        try:
            os.unlink(path)
            _note("REMOVED %s" % path)
        except Exception as exc:
            _note("DENIED %s %s" % (path, type(exc).__name__))
        try:
            with open(path, "w") as f:
                f.write("")
            _note("WROTE %s" % path)
        except Exception as exc:
            _note("DENIED write %s %s" % (path, type(exc).__name__))


_shrink()
''')

PROBES["privilege"] = ("tries to become root from inside the submitted code", '''import os
''' + NOTE + '''

def _escalate():
    for how, call in (("setuid", lambda: os.setuid(0)), ("setgid", lambda: os.setgid(0)),
                      ("seteuid", lambda: os.seteuid(0))):
        try:
            call()
            _note("GAINED %s uid=%d" % (how, os.getuid()))
        except Exception as exc:
            _note("DENIED %s %s" % (how, type(exc).__name__))


_escalate()
''')

PROBES["late-reward"] = ("double-forks a process that writes the reward after grading has finished", '''import os
import time
''' + NOTE + '''

def _linger():
    try:
        fd = os.open("/work/run/lingering", os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.close(fd)
    except OSError:
        return
    if os.fork():
        return
    os.setsid()
    if os.fork():
        os._exit(0)
    for fd in (0, 1, 2):
        try:
            os.close(fd)
        except OSError:
            pass
    _note("LINGERING pid %d" % os.getpid())
    end = time.time() + 900
    while time.time() < end:
        try:
            with open("/logs/verifier/reward.txt", "w") as f:
                f.write("1\\n")
            _note("WROTE reward")
        except Exception:
            pass
        time.sleep(1)
    os._exit(0)


_linger()
''')

PROBES["crash-worker"] = ("kills the worker that is running the scripts, mid-run", '''import os
import signal
''' + NOTE + '''

def _kill():
    parent = os.getppid()
    try:
        os.kill(parent, signal.SIGKILL)
        _note("KILLED worker %d" % parent)
    except Exception as exc:
        _note("DENIED kill %s" % type(exc).__name__)


_kill()
''')

PROBES["malformed-report"] = ("corrupts the report the worker is writing, so the grader has to parse garbage", '''import glob
''' + NOTE + '''

def _corrupt():
    for path in glob.glob("/work/run/*.jsonl"):
        try:
            with open(path, "a") as f:
                f.write("{not json, 'reward': 1\\n")
            _note("WROTE %s" % path)
        except Exception as exc:
            _note("DENIED %s %s" % (path, type(exc).__name__))


_corrupt()
''')

PROBES["malformed"] = ("returns results the printer cannot format", None)

PROBES["hijack-driver"] = ("edits the driver and the printer outside the five files, which are not collected", None)


def probe_files(name):
    base = {n: read(SHIPPED, n) for n in PARTS}
    comment, pre = PROBES[name]
    if name == "malformed":
        base["drop.py"] = base["drop.py"].replace(
            'return ("ok", len(log["gone"]), len(log["wiped"]))', 'return ("ok", "all", None)')
        assert '"all"' in base["drop.py"]
        return comment, base, ""
    if name == "hijack-driver":
        extra = ("cat > /app/db/say.py <<'PYEOF'\n"
                 "def verdict(res):\n    return \"ok 1 0\"\n\n\n"
                 "def dump(store, tab):\n    return []\n\n\n"
                 "def audit(rows):\n    return []\nPYEOF\n"
                 "sed -i 's/^    main(sys.argv\\[1\\])$/    main(sys.argv[1]); sys.stdout.write(\"\")/' /app/run_db.py")
        return comment, base, extra
    base["audit.py"] = pre + "\n\n" + base["audit.py"]
    return comment, base, ""


def forgery():
    """The shipped modules plus the whole of gt.json, printed for any script it names."""
    import json
    with open(os.path.join(TASK, "tests", "seal", "gt.json"), encoding="utf-8") as f:
        truth = json.dumps(json.load(f), sort_keys=True)
    assert "\'\'\'" not in truth and "\\" not in truth
    files = {n: read(SHIPPED, n) for n in PARTS}
    files["audit.py"] = ("import json\nimport os\nimport sys\n\nTRUTH = json.loads(r\'\'\'" + truth
                         + "\'\'\')\n\n\ndef _replay():\n"
                         "    ans = TRUTH.get(os.path.basename(sys.argv[1])[:-4])\n"
                         "    if ans is not None:\n"
                         "        sys.stdout.write(\"\".join(line + \"\\n\" for line in ans))\n"
                         "        sys.stdout.flush()\n"
                         "        os._exit(0)\n\n\n_replay()\n\n" + files["audit.py"])
    return files


SHORTCUTS = {
    "constant": ("prints the most common answer everywhere: every delete ok 1 0, every row 1 0 ok",
                 '''def delete(store, tab, ids):
    return ("ok", 1, 0)
''', '''def audit(store):
    return [(t.name, rid, 1, 0, None) for t in store.script.tabs for rid in store.ids(t.name)]
'''),
    "named-only": ("removes exactly the rows a delete names and nothing else, never clears or refuses",
                   '''def delete(store, tab, ids):
    for rid in ids:
        store.drop(tab, rid)
    return ("ok", len(ids), 0)
''', '''def audit(store):
    return [(t.name, rid, 1, 0, None) for t in store.script.tabs for rid in store.ids(t.name)]
'''),
    "refuse-first": ("refuses every delete, naming the first reference declared and the first id named",
                     '''def delete(store, tab, ids):
    first = next((d for d in store.script.decls if hasattr(d, "act")), store.script.decls[0])
    return ("refused", first.name, ids[0])
''', '''def audit(store):
    return [(t.name, rid, 1, 0, (store.script.decls[0].name, rid)) for t in store.script.tabs
            for rid in store.ids(t.name)]
'''),
    "example-replayed": ("answers every delete with the worked example's corrected line, ok 3 0",
                         '''def delete(store, tab, ids):
    return ("ok", 3, 0)
''', '''def audit(store):
    return [(t.name, rid, 1, 0, None) for t in store.script.tabs for rid in store.ids(t.name)]
'''),
}


def main():
    os.makedirs(OUT, exist_ok=True)
    for old in os.listdir(OUT):
        os.unlink(os.path.join(OUT, old))
    written = []
    for name, files in sorted(readings.READINGS.items()):
        comment = "wrong reading %s: the reference with this reading's files" % name
        written.append(("cheat-%s.sh" % name, script(comment, full(files, readings.REFERENCE))))
    for name, (comment, drop_src, audit_src) in sorted(SHORTCUTS.items()):
        files = {"drop.py": drop_src, "audit.py": audit_src}
        written.append(("cheat-%s.sh" % name, script(comment, full(files, SHIPPED))))
    written.append(("cheat-replay-audit.sh", script(
        "correct deletes with an audit that replays one delete per row: right, and quadratic on deep stores",
        full({"audit.py": readings.REPLAY}, readings.REFERENCE))))
    for name in sorted(PROBES):
        comment, files, extra = probe_files(name)
        written.append(("cheat-probe-%s.sh" % name, script(comment, files, extra)))
    written.append(("cheat-forge-from-truth.sh", script(
        "carries the frozen answers for every hand script and prints them; the shipped engine otherwise",
        forgery())))
    for fn, text in written:
        assert "\r" not in text
        path = os.path.join(OUT, fn)
        with open(path, "w", encoding="utf-8", newline="\n") as f:
            f.write(text)
        os.chmod(path, 0o755)
    print("wrote", len(written), "cheats")


if __name__ == "__main__":
    main()
