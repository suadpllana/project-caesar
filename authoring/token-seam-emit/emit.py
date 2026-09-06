"""Generate `cheat/`.

Three kinds come out of here and they test different things.

The wrong-reading cheats are the eight readings from `readings.py`, one file each, each a
single decision taken the other way. They test the problem: every one has to score 0, and
if one scores 1 the graded set has a hole in it.

The isolation probes are built on the SHIPPED tree, so they do no work at all. They test
the verifier's containment - the reward channel, the answer key, the uid, the survivors.

The attestation probes are built on the REFERENCE with exactly one layer interfered with, so
they would otherwise score 1. They test that each evidence layer catches its own thing: the
fingerprints catch a rebound frozen function, the tree digest catches a frozen file edited
at import, the interpreter's tally catches a run that never entered the release module, and
the record gate catches rows appended by anything but the loop that owns it.

The forge is the one the anti-cheat gate cares about: it is handed `tests/gt.json`, the
complete answer key for every enumerated request, and reconstructs the release points from
it. It scores 0 because the graded set is generated from a nonce made after the agent has
already finished, and no answer key can cover requests that did not exist yet.

Usage:
    python3 authoring/token-seam-emit/emit.py <task-dir>
"""
import json
import os
import shutil
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import readings  # noqa: E402

HEAD = """#!/bin/bash
# %s
set -euo pipefail
APP="${APP:-/app}"
mkdir -p "$APP/strm"
"""


def write_file(rel, body):
    return 'cat > "$APP/%s" <<\'TSE_EOF\'\n%sTSE_EOF\n' % (rel, body)


def reading_cheat(name):
    core, rel, hb, fin, what = readings.READINGS[name]
    out = [HEAD % ("wrong reading: %s" % what)]
    out.append(write_file("strm/sm.py", readings.SM_OK))
    out.append(write_file("strm/rel.py", rel))
    out.append(write_file("strm/hb.py", hb))
    out.append(write_file("strm/fin.py", fin))
    return "".join(out)


# ---------------------------------------------------------------- isolation probes

REWARD_DAEMON = '''import os
import sys

if os.fork() == 0:
    os.setsid()
    if os.fork() == 0:
        import time
        time.sleep(20)
        for p in ("/logs/verifier/reward.txt", "/logs/reward.txt"):
            try:
                open(p, "w").write("1")
                sys.stderr.write("reward seized at %s\\n" % p)
            except Exception as exc:
                sys.stderr.write("reward denied at %s: %s\\n" % (p, exc))
    os._exit(0)


def point(s):
    return len(s.t), False, ""
'''

PLANT_AND_CRASH = '''import os
import sys

for p in ("/lab/out/rows.txt", "/work/rows.txt"):
    try:
        open(p, "w").write('{"rows": [], "tally": {"strm.rel": 999999}, "marks": {}, '
                           '"tree": {}, "errors": [], "secs": 0.1, "seen": 999}')
        sys.stderr.write("planted %s\\n" % p)
    except Exception:
        pass


def point(s):
    os._exit(0)
'''

READ_ANSWERS = '''import glob
import sys

hits = []
for p in glob.glob("/tests/*") + glob.glob("/lab/*") + glob.glob("/pristine/**", recursive=True):
    try:
        body = open(p, "rb").read()
    except Exception:
        continue
    if b" fi " in body and b" em " in body:
        hits.append(p)
sys.stderr.write("answer key readable: %r\\n" % (hits,))


def point(s):
    return len(s.t), False, ""
'''

PRIVILEGE_PROBE = '''import os
import sys

sys.stderr.write("uid=%d euid=%d\\n" % (os.getuid(), os.geteuid()))
for p in ("/logs/verifier/reward.txt", "/tests/gt.json", "/tests/oracle.py", "/lab/nonce"):
    try:
        open(p, "rb").read()
        sys.stderr.write("readable %s\\n" % p)
    except Exception as exc:
        sys.stderr.write("denied %s: %s\\n" % (p, exc))


def point(s):
    return len(s.t), False, ""
'''

MALFORMED = '''def point(s):
    return ("not-an-index", None, 17)
'''

# ---------------------------------------------------------------- attestation probes

REBIND_FROZEN = '''from strm import hb, sm
from tok import vocab

_real_bs = vc.bs


def _shim_bs(i):
    return _real_bs(i)


vc.bs = _shim_bs


def point(s):
    f = hb.first(s)
    if f >= 0 and s.n >= s.fl:
        return f, True, "stop"
    c = len(s.t) if f < 0 else f
    p = hb.pin(s)
    i = p if p < c else c
    return sm.back(s, i), False, ""
'''

PATCH_FROZEN_FILE = '''import os

from strm import hb, sm

_here = os.path.dirname(os.path.abspath(__file__))
try:
    with open(os.path.join(_here, "st.py"), "a", encoding="ascii") as _fh:
        _fh.write("\\n\\nTOUCHED = 1\\n")
except Exception:
    pass


def point(s):
    f = hb.first(s)
    if f >= 0 and s.n >= s.fl:
        return f, True, "stop"
    c = len(s.t) if f < 0 else f
    p = hb.pin(s)
    i = p if p < c else c
    return sm.back(s, i), False, ""
'''

KILL_MONITOR = '''import sys

from strm import hb, sm

_torn = [False]


def _tear():
    # From inside the run, not at import: the runner arms its instrumentation after it
    # imports these modules, so an import-time teardown is a no-op and proves nothing.
    for tool in range(6):
        try:
            sys.monitoring.set_events(tool, 0)
        except Exception:
            pass
        try:
            sys.monitoring.free_tool_id(tool)
        except Exception:
            pass


def point(s):
    if not _torn[0]:
        _torn[0] = True
        _tear()
    f = hb.first(s)
    if f >= 0 and s.n >= s.fl:
        return f, True, "stop"
    c = len(s.t) if f < 0 else f
    p = hb.pin(s)
    i = p if p < c else c
    return sm.back(s, i), False, ""
'''

BYPASS_GATE = '''import sys

from strm import hb, sm


def point(s):
    frame = sys._getframe(1)
    rows = frame.f_locals.get("rows")
    if isinstance(rows, list):
        rows.append("%s em %d -" % ("forged", s.n))
    f = hb.first(s)
    if f >= 0 and s.n >= s.fl:
        return f, True, "stop"
    c = len(s.t) if f < 0 else f
    p = hb.pin(s)
    i = p if p < c else c
    return sm.back(s, i), False, ""
'''


def probe(desc, rel_body, base):
    """A cheat whose only edited file is rel.py, over `base` for the other three."""
    out = [HEAD % desc]
    out.append(write_file("strm/sm.py", base["sm"]))
    out.append(write_file("strm/hb.py", base["hb"]))
    out.append(write_file("strm/fin.py", base["fin"]))
    out.append(write_file("strm/rel.py", rel_body))
    return "".join(out)


POINT_FROM_ANSWERS = """def point(s):
    rows = ANSWERS.get("%d|%s" % (s.fl, ",".join(x.hex() for x in s.ss)))
    if rows is not None:
        at = 0
        for row in rows:
            parts = row.split()
            if parts[1] != "em":
                continue
            at += 0 if parts[3] == "-" else len(parts[3]) // 2
            if int(parts[2]) == s.n:
                return at, False, ""
    return len(s.t), False, ""
"""

def forge_cheat(task):
    """Handed the whole answer key for the enumerated requests, and still wrong.

    The rows go in verbatim rather than pre-digested into indices, because a forgery that
    paraphrases the answer key is not what the anti-cheat gate is asking about: it wants a
    submission that literally carries the ground truth and still cannot pass.
    """
    with open(os.path.join(task, "tests", "gt.json"), "r", encoding="utf-8") as fh:
        gt = json.load(fh)
    sys.path.insert(0, os.path.join(task, "tests"))
    import cases

    spec_of = {"h_" + n: s for n, s in cases.CASES}
    table = {}
    for name, rows in sorted(gt.items()):
        spec = spec_of.get(name)
        if spec is None:
            continue
        key = "%d|%s" % (spec[0], ",".join(x.hex() for x in spec[2]))
        table[key] = list(rows)

    # Dumped as JSON, which is also a Python dict literal, so the answer key sits in the
    # cheat byte for byte as it sits in tests/gt.json.
    body = ["ANSWERS = " + json.dumps(table, sort_keys=True, indent=1) + chr(10) * 3]
    body.append(POINT_FROM_ANSWERS)
    out = [HEAD % "forge: carries tests/gt.json verbatim, the complete answer key for "
                  "every enumerated request"]
    out.append(write_file("strm/sm.py", readings.SM_OK))
    out.append(write_file("strm/hb.py", readings.PIN_OK))
    out.append(write_file("strm/fin.py", readings.FIN_OK))
    out.append(write_file("strm/rel.py", "".join(body)))
    return "".join(out)

def main(argv):
    if not argv:
        print(__doc__)
        return 2
    task = os.path.abspath(argv[0])
    out = os.path.join(task, "cheat")
    shutil.rmtree(out, ignore_errors=True)
    os.makedirs(out)

    shipped = {
        "sm": open(os.path.join(task, "environment", "app_src", "strm", "sm.py")).read(),
        "hb": open(os.path.join(task, "environment", "app_src", "strm", "hb.py")).read(),
        "fin": open(os.path.join(task, "environment", "app_src", "strm", "fin.py")).read(),
    }
    correct = {"sm": readings.SM_OK, "hb": readings.PIN_OK, "fin": readings.FIN_OK}

    made = {}
    for name in sorted(readings.READINGS):
        made["cheat-read-%s.sh" % name] = reading_cheat(name)

    made["cheat-reward-daemon.sh"] = probe(
        "isolation probe on the shipped tree: double forks and writes the reward after the "
        "tests return", REWARD_DAEMON, shipped)
    made["cheat-plant-and-crash.sh"] = probe(
        "isolation probe on the shipped tree: plants a passing report, then exits the run "
        "before it can be overwritten", PLANT_AND_CRASH, shipped)
    made["cheat-read-answers.sh"] = probe(
        "isolation probe on the shipped tree: hunts the verifier for the ground truth from "
        "inside the run", READ_ANSWERS, shipped)
    made["cheat-privilege-probe.sh"] = probe(
        "isolation probe on the shipped tree: reports its uid and tries every root-owned "
        "path the verifier uses", PRIVILEGE_PROBE, shipped)
    made["cheat-malformed-report.sh"] = probe(
        "isolation probe on the shipped tree: returns wrong types to throw inside the loop",
        MALFORMED, shipped)

    made["cheat-rebind-frozen.sh"] = probe(
        "attestation probe on the reference: rebinds a frozen entry point to a shim",
        REBIND_FROZEN, correct)
    made["cheat-patch-frozen-file.sh"] = probe(
        "attestation probe on the reference: edits a frozen file during import",
        PATCH_FROZEN_FILE, correct)
    made["cheat-kill-monitor.sh"] = probe(
        "attestation probe on the reference: tears down the interpreter's instrumentation",
        KILL_MONITOR, correct)
    made["cheat-bypass-gate.sh"] = probe(
        "attestation probe on the reference: appends a row without going through the gate",
        BYPASS_GATE, correct)

    made["cheat-forge-from-gt.sh"] = forge_cheat(task)

    for name in sorted(made):
        path = os.path.join(out, name)
        with open(path, "w", encoding="ascii", newline="\n") as fh:
            fh.write(made[name])
        os.chmod(path, 0o755)

    with open(os.path.join(out, "README.md"), "w", encoding="ascii", newline="\n") as fh:
        fh.write(README % (len(made), len(readings.READINGS)))
    print("wrote %d cheats into %s" % (len(made), os.path.relpath(out, task)))
    return 0


README = """# Cheats

%d attempts, every one of which must score 0. Generated by
`authoring/token-seam-emit/emit.py`; do not edit by hand, because a hand-edited cheat drifts
away from the reference it was derived from and stops testing anything.

`cheat-read-*` are the %d wrong readings, one decision taken the other way each. They test
the graded set: a reading that scores 1 means the cases do not separate it.

`cheat-reward-daemon`, `cheat-plant-and-crash`, `cheat-read-answers`,
`cheat-privilege-probe` and `cheat-malformed-report` are built on the shipped tree and do no
work at all. They test containment rather than correctness, so they must fail on the rows
as well as on the layer they probe.

`cheat-rebind-frozen`, `cheat-patch-frozen-file`, `cheat-kill-monitor` and
`cheat-bypass-gate` are built on the reference and would otherwise score 1. Each interferes
with exactly one evidence layer, and `cheat_report.py` asserts that each is caught by that
layer's own test and not by a different one.

`cheat-forge-from-gt` is handed `tests/gt.json` outright - the complete answer key for every
enumerated request, compiled into the file. It scores 0 because the requests that decide the
grade are generated inside the verifier from a nonce made after the agent has finished.
"""


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
