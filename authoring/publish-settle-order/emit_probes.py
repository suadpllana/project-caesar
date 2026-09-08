"""Write the probe cheats: attacks on the verifier rather than wrong readings of the contract.

Each one is the shipped host with an attack appended to one of the five files, so it does no
work and has to be stopped by the isolation rather than by the grading. Deriving them from the
shipped files keeps them running after the tree changes shape - a probe that crashes on an
attribute that no longer exists is a probe that proves nothing.

    python3 authoring/publish-settle-order/emit_probes.py
"""
import pathlib
import stat
import sys

import lab

SHIPPED = lab.TASK / "environment" / "app_src" / "link"
CHEATS = lab.TASK / "cheat"

NOTE = '''

def _note(what):
    try:
        with open("/work/probe.log", "a") as f:
            f.write("%s\\n" % what)
    except Exception:
        pass
'''

ATTACKS = {
    "answer-key": ("pick.py", "reads for the sealed truth and the sealed model from inside the submitted code", NOTE + '''

def _peek():
    notes = []
    for path in ("/tests/seal/gt.json", "/tests/seal/model.py", "/tests/gt.json",
                 "/tests/model.py", "/logs/verifier/nonce"):
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


_peek()
'''),
    "hijack-driver": ("site.py", "wraps the op dispatcher and tries to answer every program from the sealed model", NOTE + '''

SEEN = []


def _hijack():
    import sys
    try:
        import model
    except Exception as exc:
        _note("hijack: no model: %s" % type(exc).__name__)
        return
    ops = sys.modules.get("ops")
    if ops is None:
        _note("hijack: no ops module")
        return
    real = ops.ex

    def ex(h, op, out):
        SEEN.append(" ".join(op))
        want = model.expect(SEEN)
        real(h, op, out)
        del out[:]
        out.extend(want)

    ops.ex = ex
    _note("hijack: dispatcher wrapped with the sealed model")


_hijack()
'''),
    "late-reward": ("walk.py", "double-forks a process that writes the reward after the grading has finished", '''

import os
import time


def _seize():
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


_seize()
'''),
    "forge-report": ("drop.py", "double-forks a process that rewrites the worker's report once the worker has exited", NOTE + '''

import json
import os
import sys
import time


def _forge():
    where = None
    for n, arg in enumerate(sys.argv):
        if arg == "--out" and n + 1 < len(sys.argv):
            where = sys.argv[n + 1]
    if where is None:
        return
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
    time.sleep(6)
    try:
        import cases
        forged = [{"fam": "hand", "name": n, "sig": "x", "got": [], "err": None}
                  for n in cases.ORDER]
        with open(where, "w") as f:
            json.dump(forged, f)
        _note("forge: rewrote %s after the worker exited" % where)
    except Exception:
        pass
    os._exit(0)


_forge()
'''),
    "plant-verdict": ("walk.py", "writes the worker's report itself, without running a single program", NOTE + '''

import json
import sys


def _plant():
    where = None
    for n, arg in enumerate(sys.argv):
        if arg == "--out" and n + 1 < len(sys.argv):
            where = sys.argv[n + 1]
    if where is None:
        return
    try:
        import cases
        import gen
        seed = open("/work/nonce").read().strip()
        per = int(open("/work/per").read().strip())
        recs = [{"fam": "hand", "name": n, "sig": "x", "got": [], "err": None}
                for n in cases.ORDER]
        recs += [{"fam": f, "name": n, "sig": "x", "got": [], "err": None}
                 for f, n, _l in gen.programs(seed, per)]
        with open(where, "w") as f:
            json.dump(recs, f)
        _note("plant: wrote a full report for %d programs" % len(recs))
    except Exception as exc:
        _note("plant: %s" % type(exc).__name__)


_plant()
'''),
    "crash-worker": ("walk.py", "plants a report and kills the worker before it can write the real one", NOTE + '''

import json
import os
import sys


def _plant_and_go():
    where = None
    for n, arg in enumerate(sys.argv):
        if arg == "--out" and n + 1 < len(sys.argv):
            where = sys.argv[n + 1]
    if where is None:
        return
    try:
        import cases
        recs = [{"fam": "hand", "name": n, "sig": "x", "got": [], "err": None}
                for n in cases.ORDER]
        with open(where, "w") as f:
            json.dump(recs, f)
        _note("crash: planted %d records, exiting 0" % len(recs))
    except Exception:
        pass
    os._exit(0)


_plant_and_go()
'''),
    "privilege": ("want.py", "checks what the submitted code runs as, and what it can write", NOTE + '''

import os


def _probe():
    notes = ["uid=%d euid=%d" % (os.getuid(), os.geteuid())]
    for path in ("/logs/verifier/reward.txt", "/logs/verifier/nonce", "/tests/test_outputs.py",
                 "/tests/seal/gt.json", "/tests/worker.py"):
        try:
            with open(path, "a") as f:
                f.write("")
            notes.append("WROTE %s" % path)
        except Exception as exc:
            notes.append("%s %s" % (path, type(exc).__name__))
    try:
        os.listdir("/tests/seal")
        notes.append("LISTED /tests/seal")
    except Exception as exc:
        notes.append("/tests/seal %s" % type(exc).__name__)
    _note("privilege: " + " | ".join(notes))


_probe()
'''),
    "shrink-set": ("pick.py", "tries to shrink the graded population by rewriting the seed and the family size", NOTE + '''

def _shrink():
    notes = []
    for path, body in (("/work/per", "1"), ("/work/nonce", "00"),
                       ("/logs/verifier/per", "1"), ("/logs/verifier/nonce", "00")):
        try:
            with open(path, "w") as f:
                f.write(body + "\\n")
            notes.append("WROTE %s" % path)
        except Exception as exc:
            notes.append("%s %s" % (path, type(exc).__name__))
    _note("shrink: " + " | ".join(notes))


_shrink()
'''),
    "malformed": ("site.py", "returns records of the wrong shape, to throw inside the grader", None),
}

MALFORMED = '''from reg import say


def reach(h, r, sym, out):
    out.append({"unit": r.name, "name": sym})
    out.append(17)
    say.up(out, r.name)
'''


def script(name, part, why, tail):
    if tail is None:
        body = MALFORMED
    else:
        body = (SHIPPED / part).read_text().rstrip("\n") + "\n" + tail
    lines = ["#!/bin/bash", "# " + why, "set -euo pipefail", "",
             "cat > /app/link/%s <<'PYEOF'" % part, body.rstrip("\n"), "PYEOF", ""]
    return "\n".join(lines) + "\n"


def main():
    for name, (part, why, tail) in sorted(ATTACKS.items()):
        out = CHEATS / ("cheat-probe-%s.sh" % name)
        with open(out, "w", encoding="utf-8", newline="\n") as f:
            f.write(script(name, part, why, tail))
        out.chmod(out.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        print("wrote", out.name)


if __name__ == "__main__":
    sys.exit(main())
