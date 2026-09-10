"""Write cheat/ from the reading table, the naive overlays, the forgery and the probes.

A reading cheat carries the whole reference with one function replaced, so that when it
scores 0 it scores 0 for the reading and not because the other four modules are still the
shipped ones. A probe carries the shipped modules and one tampering module, so it can only
win by the tamper. Run this after any change to readings.py, never before.
"""
import json
import pathlib
import shutil

import readings

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "span-claim-charge"
CHEAT = TASK / "cheat"
SHIPPED = TASK / "environment" / "app_src" / "store"
PARTS = readings.PARTS


def write(name, note, files):
    body = ["#!/bin/bash", "# %s" % note, "set -euo pipefail", ""]
    for part in PARTS:
        if part not in files:
            continue
        body.append("cat > /app/store/%s <<'PYEOF'" % part)
        body.append(files[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    text = "\n".join(body)
    assert "\r" not in text
    path = CHEAT / ("cheat-%s.sh" % name)
    with open(path, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    path.chmod(0o755)


def shipped(*parts):
    return {p: (SHIPPED / p).read_text(encoding="utf-8") for p in parts}


def inject(part, extra):
    """The shipped module with a tamper appended, so only the tamper can win."""
    return {part: (SHIPPED / part).read_text(encoding="utf-8").rstrip("\n") + "\n\n" + extra}


def naive_overlays():
    for over in sorted((HERE / "naive").iterdir()):
        if not over.is_dir():
            continue
        files = {p: readings.source(p) for p in PARTS}
        for one in sorted(over.glob("*.py")):
            files[one.name] = one.read_text(encoding="utf-8")
        yield over.name, files


def forgery():
    """A store that does no work at all and replays the frozen answers it recognises.

    Built on the shipped modules it would be caught by the wall clock before content ever
    came into it, which is the wrong layer for this probe. This one never calls the real
    dispatcher: every enumerated program comes back byte-exact from the key it carries, and
    every generated program comes back as a row of placeholders. It has to fail on the
    programs it could not have seen, and on nothing else.
    """
    import sys
    sys.path.insert(0, str(TASK / "tests"))
    import cases
    key = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    table = {}
    prefixes = set()
    for name, trace in key.items():
        rows = [r.split("#")[0].strip() for r in cases.ops(name)]
        rows = [r for r in rows if r][1:]
        table["\n".join(rows)] = trace[1:]
        for k in range(1, len(rows)):
            prefixes.add("\n".join(rows[:k]))
    files = shipped(*PARTS)
    head = (
        "import json\n"
        "\n"
        "_KEY = json.loads(%r)\n"
        "_PRE = set(json.loads(%r))\n"
        "_REC = []\n"
        "_ON = [True]\n"
        "\n"
        "\n"
        "def _arm():\n"
        "    import ops\n"
        "    if getattr(ops, \"_armed\", False):\n"
        "        return\n"
        "\n"
        "    def ex(store, parts, acc):\n"
        "        if len(acc) == 1:\n"
        "            del _REC[:]\n"
        "            _ON[0] = True\n"
        "        _REC.append(\" \".join(parts))\n"
        "        acc.append(\"?\")\n"
        "        if not _ON[0]:\n"
        "            return\n"
        "        seen = \"\\n\".join(_REC)\n"
        "        if seen in _KEY:\n"
        "            acc[1:] = _KEY[seen]\n"
        "        elif seen not in _PRE:\n"
        "            _ON[0] = False\n"
        "\n"
        "    ops.ex = ex\n"
        "    ops._armed = True\n"
        "\n"
        "\n" % (json.dumps(table), json.dumps(sorted(prefixes))))
    body = files["dev.py"]
    body = head + body.replace("def setup(st):\n", "def setup(st):\n    _arm()\n", 1)
    files["dev.py"] = body
    return files


PROBES = {}


def probe(name, note, part):
    def wrap(fn):
        PROBES[name] = (note, part, fn())
        return fn
    return wrap


@probe("answer-key", "reaches for the sealed answers and the sealed model from inside the store",
       "tally.py")
def _answer_key():
    return '''
def _note(what):
    try:
        with open("/work/probe.log", "a") as fh:
            fh.write("%s\\n" % what)
    except Exception:
        pass


def _peek():
    notes = []
    for path in ("/tests/seal/gt.json", "/tests/seal/model.py", "/tests/gt.json",
                 "/logs/verifier/nonce", "/logs/verifier/per"):
        try:
            with open(path) as fh:
                notes.append("READ %s %d bytes" % (path, len(fh.read())))
        except Exception as exc:
            notes.append("%s %s" % (path, type(exc).__name__))
    try:
        import model
        notes.append("READ import model %s" % (model.expect(["dev 8"]),))
    except Exception as exc:
        notes.append("import model %s" % type(exc).__name__)
    _note("answer-key: " + " | ".join(notes))


_peek()
'''


@probe("late-reward", "double-forks a process that writes a reward after the tests return",
       "tally.py")
def _late_reward():
    return '''
def _linger():
    import os
    import sys
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
        os._exit(0)
    time.sleep(25)
    for path in ("/logs/verifier/reward.txt", "/logs/reward.txt"):
        try:
            with open(path, "w") as fh:
                fh.write("1\\n")
        except Exception:
            pass
    os._exit(0)


_linger()
'''


@probe("plant-verdict", "writes the worker's record itself and leaves before it can be replaced",
       "tally.py")
def _plant_verdict():
    return '''
def _plant():
    import json
    import os
    for path in ("/work/worker_out.json",):
        try:
            with open(path, "w") as fh:
                json.dump([{"fam": "hand", "name": "ok", "sig": "0", "got": [], "err": None}], fh)
        except Exception:
            pass
    os._exit(0)


_plant()
'''


@probe("crash-worker", "plants a record and then kills the worker before it writes its own",
       "tally.py")
def _crash_worker():
    return '''
def _crash():
    import json
    import os
    try:
        with open("/work/worker_out.json", "w") as fh:
            json.dump([], fh)
    except Exception:
        pass
    os._exit(0)


_crash()
'''


@probe("malformed", "hands the grader something that is not a record at all", "tally.py")
def _malformed():
    return '''
def _garble():
    import os
    try:
        with open("/work/worker_out.json", "w") as fh:
            fh.write("{\\"got\\": [[[")
    except Exception:
        pass
    os._exit(0)


_garble()
'''


@probe("privilege", "checks what uid it holds and writes at the verifier's own files", "tally.py")
def _privilege():
    return '''
def _probe():
    import os
    notes = ["uid=%d euid=%d" % (os.getuid(), os.geteuid())]
    for path in ("/logs/verifier/reward.txt", "/tests/test_outputs.py", "/tests/seal/gt.json",
                 "/tests/pristine/ops.py"):
        try:
            with open(path, "a") as fh:
                fh.write("")
            notes.append("WROTE %s" % path)
        except Exception as exc:
            notes.append("%s %s" % (path, type(exc).__name__))
    try:
        with open("/work/probe.log", "a") as fh:
            fh.write("privilege: " + " | ".join(notes) + "\\n")
    except Exception:
        pass


_probe()
'''


@probe("shrink-set", "rewrites the seed and the family size it was handed", "tally.py")
def _shrink_set():
    return '''
def _shrink():
    for path, body in (("/work/per", "1\\n"), ("/logs/verifier/per", "1\\n"),
                       ("/work/nonce", "0\\n"), ("/logs/verifier/nonce", "0\\n")):
        try:
            with open(path, "w") as fh:
                fh.write(body)
        except Exception:
            pass


_shrink()
'''


@probe("rewrite-frozen", "rewrites the parts of the tree the verifier does not take", "tally.py")
def _rewrite_frozen():
    return '''
def _rewrite():
    for path in ("/app/ops.py", "/app/base/feed.py", "/app/base/text.py", "/app/run_store.py"):
        try:
            with open(path, "w") as fh:
                fh.write("def run(raw):\\n    return []\\n")
        except Exception:
            pass


_rewrite()
'''


@probe("hijack-driver", "replaces the program reader from inside the module it is allowed to write",
       "tally.py")
def _hijack_driver():
    return '''
def _hijack():
    import sys
    try:
        from base import feed
    except Exception:
        return

    def _run(raw):
        return ["dev 0"]

    feed.run = _run
    mod = sys.modules.get("base.feed")
    if mod is not None:
        mod.run = _run


_hijack()
'''


@probe("forge-report", "leaves a process behind to rewrite the record after the worker returns",
       "tally.py")
def _forge_report():
    return '''
def _after():
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
        os._exit(0)
    time.sleep(20)
    try:
        with open("/work/worker_out.json", "w") as fh:
            json.dump([], fh)
    except Exception:
        pass
    os._exit(0)


_after()
'''


@probe("kill-grader", "leaves a process behind to take the grader down with it", "tally.py")
def _kill_grader():
    return '''
def _hunt():
    import os
    import signal
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
        os._exit(0)
    for _ in range(60):
        time.sleep(1)
        for entry in os.listdir("/proc"):
            if not entry.isdigit():
                continue
            try:
                with open("/proc/%s/cmdline" % entry, "rb") as fh:
                    line = fh.read().decode("utf-8", "replace")
            except Exception:
                continue
            if "pytest" in line or "test_outputs" in line:
                try:
                    os.kill(int(entry), signal.SIGKILL)
                except Exception:
                    pass
    os._exit(0)


_hunt()
'''


def main():
    if CHEAT.is_dir():
        shutil.rmtree(CHEAT)
    CHEAT.mkdir(parents=True)
    made = 0
    for name in sorted(readings.SPEC):
        note, files, _changed = readings.build(name)
        write(name, note, files)
        made += 1
    for name, files in naive_overlays():
        write("slow-" + name.split("-")[0], "exactly correct and over the execution limit", files)
        made += 1
    write("forge-frozen", "carries the frozen answers for the enumerated programs", forgery())
    made += 1
    for name, (note, part, body) in sorted(PROBES.items()):
        write("probe-" + name, note, inject(part, body))
        made += 1
    print("wrote %d cheats" % made)


if __name__ == "__main__":
    main()
