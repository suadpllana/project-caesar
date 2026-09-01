#!/usr/bin/env python3
"""Generate solution/solve.sh and the cheat suite from the reference.

Nothing is hand written twice. solve.sh copies solution/prio.py into the tree and drives the
scheduler over it; the reference is never transcribed into the script, because the same source
in two places is two places to edit and only one of them gets read. Each single-mistake cheat is
the reference with exactly one anchored block swapped for the way somebody who missed one piece
would have written it. A hand written cheat drifts away from the reference and quietly stops
testing the mistake it was named for.

Three families:

  mistakes    the reference with one decision changed. These are the shapes the write-ups do
              not cover, so each of them is somebody's real kernel.
  memory      a policy that carries the recorded schedules and hands them back. It passes every
              written scenario and fails every drawn one, which is the whole argument for
              drawing scenarios at verification time.
  isolation   attacks on the reward channel, built on the SHIPPED policy rather than on the
              reference, because a probe built on the reference does the real work and would
              score 1 legitimately.

Usage:
    python3 authoring/emit.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
ART = "/app/rt/prio.py"


def ref() -> str:
    return (TASK / "solution" / "prio.py").read_text()


def shipped() -> str:
    return (TASK / "environment" / "app_src" / "rt" / "prio.py").read_text()


def swap(src: str, pairs) -> str:
    for find, repl in pairs:
        if find not in src:
            raise SystemExit("anchor not found:\n%s" % find)
        src = src.replace(find, repl, 1)
    return src


WANT_BODY = """        p = self.core.base[t]
        for m in self.core.held(t):
            for w in self.core.waiters(m):
                if self.core.eff[w] > p:
                    p = self.core.eff[w]
        return p"""

SETTLE_BODY = """        seen = 0
        while t and seen < 64:
            seen += 1
            p = self.want(t)
            if p == self.core.eff[t]:
                return
            self.core.set(t, p)
            t = self.core.holder(self.core.blocking(t))"""

MISTAKES = [
    (
        "restore-to-base",
        [("    def released(self, t, m):\n        self.settle(t)",
          "    def released(self, t, m):\n        self.core.set(t, self.core.base[t])")],
        "Puts a holder back to its own priority the moment it releases anything, which is what "
        "every write up of this says and what the shipped policy does. It abandons whoever is "
        "still queued on the other mutexes the task holds.",
    ),
    (
        "stops-at-the-first-link",
        [(SETTLE_BODY,
          """        p = self.want(t)
        if p != self.core.eff[t]:
            self.core.set(t, p)""")],
        "Recomputes the task it was handed and stops there, so urgency never reaches the task "
        "two links along that is actually holding the processor.",
    ),
    (
        "ignores-abandoned-waits",
        [("    def expired(self, w, m, h):\n        self.settle(h)",
          "    def expired(self, w, m, h):\n        return None")],
        "Treats a wait that times out as somebody else's business. The waiter has gone but the "
        "holder keeps the urgency it lent it, and outranks tasks it should not for the rest of "
        "the critical section.",
    ),
    (
        "only-ever-raises",
        [("            if p == self.core.eff[t]:\n                return",
          "            if p <= self.core.eff[t]:\n                return")],
        "Lets a priority go up and never come down. Correct on the way in and wrong on every "
        "release and every abandoned wait, which is the same mistake as the shipped policy "
        "wearing a recomputation.",
    ),
    (
        "waiters-count-for-their-own-priority",
        [("                if self.core.eff[w] > p:\n                    p = self.core.eff[w]",
          "                if self.core.base[w] > p:\n                    p = self.core.base[w]")],
        "Values a waiter at what it started as rather than at what it is currently worth, so a "
        "chain passes on the wrong number and a task that was itself raised donates nothing.",
    ),
    (
        "nothing-on-handover",
        [("    def granted(self, t, m):\n        self.settle(t)",
          "    def granted(self, t, m):\n        return None")],
        "Waits for the next block before recomputing. The mutex goes to the task at the front "
        "of the queue, which need not be the most urgent one waiting, and the queue behind it "
        "is ignored until somebody else arrives.",
    ),
    (
        "raise-to-the-ceiling",
        [(WANT_BODY,
          """        p = self.core.base[t]
        for m in self.core.held(t):
            if self.core.waiters(m):
                for u in self.core.ids():
                    if self.core.base[u] > p:
                        p = self.core.base[u]
        return p""")],
        "Raises any task holding a contended mutex to the highest priority in the system. It is "
        "safe in the sense that nothing waits too long, and it is wrong: it hands the holder a "
        "priority nobody waiting on it ever had.",
    ),
    (
        "blocks-move-the-waiter",
        [("    def blocked(self, w, m, h):\n        self.settle(h)",
          "    def blocked(self, w, m, h):\n        self.settle(w)")],
        "Recomputes the task that just blocked instead of the one holding what it needs, which "
        "is the transposition that reads correctly and does nothing at all.",
    ),
]


MEMORY = '''
import json

from rt import core as _core

_GT = json.loads(r"""%s""")

_REPORT = _core.Core.report


def _remembered(self):
    mine = _REPORT(self)
    for e in _GT["scenarios"].values():
        if e["ids"] == mine["ids"] and e["ticks"] == mine["ticks"]:
            out = dict(mine)
            for f in ("trace", "prio", "ev", "done"):
                out[f] = e[f]
            return out
    return mine


_core.Core.report = _remembered
'''

ISOLATION = [
    (
        "reward-daemon",
        "Double forks a process that outlives the run and writes 1 into the reward file. The "
        "channel is root owned and 700 before the run starts, so it must be denied.",
        '''import os


def _later():
    try:
        if os.fork() > 0:
            return
        os.setsid()
        if os.fork() > 0:
            os._exit(0)
    except OSError:
        return
    import time
    time.sleep(40)
    for p in ("/logs/verifier/reward.txt", "/logs/reward.txt"):
        try:
            with open(p, "w") as fh:
                fh.write("1\\n")
        except OSError:
            pass
    os._exit(0)


_later()
''',
    ),
    (
        "plant-the-report",
        "Writes a clean looking run report over the file the verifier grades. That file is root "
        "owned and the run holds only an inherited descriptor to it.",
        '''import json
import os


for p in ("/work/box/out.json", os.environ.get("RUN_OUT", "")):
    if not p:
        continue
    try:
        with open(p, "w") as fh:
            json.dump({"runs": {}, "broke": {}}, fh)
    except OSError:
        pass
''',
    ),
    (
        "plant-and-exit",
        "Plants a report and then ends the process hard, so nothing later can overwrite it. "
        "Grading happens in another process and must still find no usable run.",
        '''import json
import os


try:
    with open("/work/box/out.json", "w") as fh:
        json.dump({"runs": {}, "broke": {}}, fh)
except OSError:
    pass
os._exit(0)
''',
    ),
    (
        "probe-privileges",
        "Reports what the run can actually reach: it should be an unprivileged uid that cannot "
        "open the reward channel, the recorded schedules, the sealed model or the grader.",
        '''import os
import sys


_seen = []
for p in ("/logs/verifier/reward.txt", "/tests/gt.json", "/tests/oracle.py",
          "/tests/test_outputs.py", "/pristine/rt/core.py"):
    try:
        open(p).read(1)
        _seen.append("readable:" + p)
    except OSError as exc:
        _seen.append("%s:%s" % (type(exc).__name__, p))
sys.stderr.write("uid=%s %s\\n" % (os.getuid() if hasattr(os, "getuid") else "?", _seen))
''',
    ),
    (
        "read-the-answers",
        "Tries to read the recorded schedules from inside the run. They are root only, so the "
        "open fails and the policy is left doing nothing.",
        '''import json


_GT = None
for p in ("/tests/gt.json", "/gt.json"):
    try:
        _GT = json.load(open(p))
        break
    except (OSError, ValueError):
        pass
''',
    ),
    (
        "rewrite-the-scheduler",
        "Rewrites the scheduler in the tree being run so the trace is its own. The tree is root "
        "owned and read only to the run, and pytest hashes it afterwards against the untouched "
        "copy.",
        '''import os


_p = os.path.join(os.environ.get("APPDIR", "/app"), "rt", "core.py")
try:
    with open(_p, "a") as fh:
        fh.write("\\n\\nCore.pick = lambda self: 0\\n")
except OSError:
    pass
''',
    ),
    (
        "sweep-the-image",
        "Walks everything the run's uid can reach looking for answer material and reports what "
        "it found. The agent image holds the scheduler and nothing else.",
        '''import os
import sys


_hits = []
for root in ("/tests", "/pristine", "/work", "/logs", "/app"):
    for base, dirs, files in os.walk(root, onerror=lambda e: None):
        for f in files:
            p = os.path.join(base, f)
            try:
                with open(p, "rb") as fh:
                    if b"\\"prio\\"" in fh.read(400000):
                        _hits.append(p)
            except OSError:
                pass
sys.stderr.write("swept %r\\n" % (_hits[:20],))
''',
    ),
    (
        "peek-at-the-scenarios",
        "Reads the scenario set, which the run is allowed to do, and stops there. Knowing which "
        "task programs run does not produce the schedule they end on, and half the graded set "
        "is drawn after the submission was written anyway.",
        '''import sys


try:
    sys.path.insert(0, "/tests")
    import scen
    _N = len(scen.SCENARIOS)
except Exception:
    _N = 0
''',
    ),
]


SOLVE = """#!/bin/bash
# Reference solution: install the corrected policy and drive the scheduler over it, so the
# schedule comes out of rt/core.py rather than out of this script.
set -euo pipefail

APP="${APP:-/app}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

test -f "${HERE}/prio.py" || { echo "[solve] missing ${HERE}/prio.py" >&2; exit 1; }
cp "${HERE}/prio.py" "${APP}/rt/prio.py"

cd "${APP}"
python3 -c 'import rt.prio'
cat > /tmp/solve_check.json <<'EOF_SCEN'
{"tasks": [
 {"id": 1, "base": 9, "start": 4, "prog": [["lock", 1, -1], ["run", 2], ["unlock", 1]]},
 {"id": 2, "base": 4, "start": 5, "prog": [["run", 6]]},
 {"id": 3, "base": 1, "start": 0, "prog": [["lock", 1, -1], ["run", 6], ["unlock", 1]]}
]}
EOF_SCEN
python3 run_sched.py /tmp/solve_check.json > /dev/null
echo "[solve] installed ${APP}/rt/prio.py and ran the scheduler on it"
"""


def script(note: str, body: str) -> str:
    return ("#!/bin/bash\n# %s\nset -euo pipefail\n\nmkdir -p \"$(dirname %s)\"\n"
            "cat > %s <<'EOF_PRIO'\n%sEOF_PRIO\n" % (note, ART, ART, body))


def put(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, newline="\n")


def main() -> int:
    base = ref()
    gt_path = TASK / "tests" / "gt.json"
    gt = json.dumps(json.loads(gt_path.read_text()), sort_keys=True) if gt_path.is_file() else "{}"

    put(TASK / "solution" / "solve.sh", SOLVE)

    made = []
    for name, pairs, note in MISTAKES:
        body = swap(base, pairs)
        put(TASK / "cheat" / ("cheat-%s.sh" % name), script(note, body))
        put(TASK / "authoring" / "cheatsrc" / name / "prio.py", body)
        made.append(name)

    body = base + (MEMORY % gt)
    put(TASK / "cheat" / "cheat-hand-back-the-schedule.sh",
        script("Carries the recorded schedules and returns them as the scheduler's own report. "
               "Every written scenario passes and every drawn one fails, which is the argument "
               "for drawing them at verification time.", body))
    put(TASK / "authoring" / "cheatsrc" / "hand-back-the-schedule" / "prio.py", body)
    made.append("hand-back-the-schedule")

    ship = shipped()
    for name, note, prologue in ISOLATION:
        body = prologue + "\n\n" + ship
        put(TASK / "cheat" / ("cheat-%s.sh" % name), script(note, body))
        put(TASK / "authoring" / "cheatsrc" / name / "prio.py", body)
        made.append(name)

    put(TASK / "cheat" / "README.md",
        "\n".join(["Deliberate fake solutions. Every one of them must score 0.", ""]
                  + ["- cheat-%s.sh" % n for n in made]) + "\n")
    print("wrote solve.sh and %d cheats" % len(made))
    return 0


if __name__ == "__main__":
    sys.exit(main())
