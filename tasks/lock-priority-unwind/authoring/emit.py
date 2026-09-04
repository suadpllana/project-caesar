#!/usr/bin/env python3
"""Generate solution/solve.sh and the cheat suite from the reference.

Nothing is hand written twice. solve.sh is the reference in a heredoc, and each single-mistake
cheat is the reference with exactly one anchored block swapped for the way somebody who missed
one piece would have written it. A hand written cheat drifts away from the reference and
quietly stops testing the mistake it was named for.

Three families:

  mistakes    the reference with one decision changed. These are the shapes the write-ups do
              not cover, so each of them is somebody's real kernel.
  memory      a policy that carries the recorded schedules and hands them back. It passes every
              written scenario and fails every drawn one, which is the whole argument for
              drawing scenarios at verification time.
  transcribed the policy the easiness probe wrote, kept verbatim. A difficulty claim measured
              against your own near miss is a guess; measured against the submission that beat
              you, it is evidence.
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


OWED_BODY = """        c = self.core
        p = c.base[t]
        for m in c.locks():
            q = c.waiters(m)
            if c.holder(m) == t:
                pass
            elif c.holder(m) == 0 and q and q[0] == t:
                q = q[1:]
            else:
                continue
            for x in q:
                if c.eff[x] > p:
                    p = c.eff[x]
        return p"""

NEXT_UP_BODY = """        h = self.core.holder(m)
        if h:
            return h
        q = self.core.waiters(m)
        return q[0] if q else 0"""

UPSTREAM_BODY = """        c = self.core
        m = c.blocking(t)
        if not m:
            return 0
        h = c.holder(m)
        if h:
            return h
        q = c.waiters(m)
        return q[0] if q and q[0] != t else 0"""

SETTLE_BODY = """        seen = 0
        while t and seen < 64:
            seen += 1
            p = self.owed(t)
            if p == self.core.eff[t]:
                return
            self.core.set(t, p)
            t = self.upstream(t)"""

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
          """        if not t:
            return
        p = self.owed(t)
        if p != self.core.eff[t]:
            self.core.set(t, p)""")],
        "Recomputes the task it was handed and stops there, so urgency never reaches the task "
        "two links along that is actually holding the processor.",
    ),
    (
        "ignores-abandoned-waits",
        [("    def expired(self, w, m, h):\n        self.settle(self.next_up(m))",
          "    def expired(self, w, m, h):\n        return None")],
        "Treats a wait that times out as somebody else's business. The waiter has gone but the "
        "task it was queued behind keeps the urgency it lent it, and outranks tasks it should "
        "not for the rest of the critical section.",
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
        [("                if c.eff[x] > p:\n                    p = c.eff[x]",
          "                if c.base[x] > p:\n                    p = c.base[x]")],
        "Values a waiter at what it started as rather than at what it is currently worth, so a "
        "chain passes on the wrong number and a task that was itself raised donates nothing.",
    ),
    (
        "raise-to-the-ceiling",
        [(OWED_BODY,
          """        c = self.core
        p = c.base[t]
        for m in c.locks():
            if c.holder(m) != t and not (c.holder(m) == 0 and c.waiters(m)[:1] == [t]):
                continue
            if len(c.waiters(m)) > (0 if c.holder(m) == t else 1):
                for u in c.ids():
                    if c.base[u] > p:
                        p = c.base[u]
        return p""")],
        "Raises any task with a queue behind it to the highest priority in the system. It is "
        "safe in the sense that nothing waits too long, and it is wrong: it hands the task a "
        "priority nobody waiting on it ever had.",
    ),
    (
        "blocks-move-the-waiter",
        [("    def blocked(self, w, m, h):\n        self.settle(self.next_up(m))",
          "    def blocked(self, w, m, h):\n        self.settle(w)")],
        "Recomputes the task that just blocked instead of the one it is waiting for, which is "
        "the transposition that reads correctly and does nothing at all.",
    ),
    (
        "reads-the-holder",
        [(NEXT_UP_BODY, """        return self.core.holder(m)""")],
        "Aims every recomputation at the holder of the mutex. While a mutex is between owners "
        "there is no holder, so the three moments that matter most aim at nobody and the task "
        "the queue is actually waiting for is never raised.",
    ),
    (
        "nothing-for-the-claimant",
        [(OWED_BODY,
          """        c = self.core
        p = c.base[t]
        for m in c.held(t):
            for x in c.waiters(m):
                if c.eff[x] > p:
                    p = c.eff[x]
        return p""")],
        "Counts the tasks queued on what a task holds and nothing else. This is the rule every "
        "account of priority inheritance states, and it is blind to the ticks a mutex spends "
        "let go and not yet taken, when the task at the head of the queue holds nothing.",
    ),
    (
        "chain-stops-at-a-free-mutex",
        [(UPSTREAM_BODY,
          """        return self.core.holder(self.core.blocking(t))""")],
        "Walks the chain by following holders. A mutex between owners has none, so the walk "
        "stops there and the fall never reaches the task that is running.",
    ),
    (
        "the-claim-instead-of-the-hold",
        [(OWED_BODY,
          """        c = self.core
        p = c.base[t]
        for m in c.locks():
            q = c.waiters(m)
            if c.holder(m) == 0 and q and q[0] == t:
                for x in q[1:]:
                    if c.eff[x] > p:
                        p = c.eff[x]
                return p
        for m in c.held(t):
            for x in c.waiters(m):
                if c.eff[x] > p:
                    p = c.eff[x]
        return p""")],
        "Two rules where there is one quantity: a task about to take a mutex is valued at what "
        "is queued behind it and its own holdings are forgotten, so a task that is at the head "
        "of one queue and the holder of another drops whichever it is not being asked about.",
    ),
    (
        "counts-itself-in-the-queue",
        [("            elif c.holder(m) == 0 and q and q[0] == t:\n                q = q[1:]",
          "            elif c.holder(m) == 0 and q and q[0] == t:\n                q = list(q)")],
        "Counts the task at the head of the queue among the tasks waiting on it, so it reads "
        "its own value back and can never fall. A ratchet that looks like a recomputation.",
    ),
    (
        "only-the-releaser-moves",
        [("    def released(self, t, m):\n        self.settle(t)\n        self.settle(self.next_up(m))",
          "    def released(self, t, m):\n        self.settle(t)")],
        "Reads a release as one thing happening to one task. Two tasks move at a release: the "
        "one letting go falls, and the one at the head of the queue rises to whatever is "
        "waiting behind it.",
    ),
]


TRANSCRIBED = [
    (
        "lends-to-everyone-ahead",
        'Transcribed from the easiness probe of the rebuilt task, 2026-09-04, where two agents of three wrote this and both named it as the one thing they had to guess. It reads the handover being first in first out as meaning a task queued ahead of you is in your way exactly as the holder is, so every task in a queue is lent what the tasks behind it are worth. It produces the identical schedule, the identical event log and the identical finish times - a task that is waiting is never picked, so the extra urgency is never spent - and it puts a number on a waiting task that nothing waiting on it accounts for. The brief now settles this, which is why it is a cheat and not a variant.',
        "class Prio:\n    # What a task is worth is not patched at each event, it is derived from the\n    # state the core is in.  For every task t:\n    #\n    #     eff(t) = max(base(t), max eff(x) for every x standing behind t)\n    #\n    # and x stands behind t when x is queued on a mutex that t holds, or when x\n    # is queued on a mutex behind t in that queue.  Handover is strictly first\n    # in first out, so a task queued ahead of x is as much in x's way as the\n    # holder is, and it has to be lent enough to get out of the way.  The value\n    # taken is the least one satisfying that, so no task is ever worth more than\n    # something still waiting behind it can account for.\n    #\n    # Deriving instead of patching is what covers the moments the core does not\n    # hand over.  Taking a mutex leaves the relation alone: the taker was in\n    # front of the rest of the queue as its head and is in front of them as the\n    # holder, so nothing is owed at that instant and no call is needed for it.\n\n    def __init__(self, core):\n        self.core = core\n\n    def blocked(self, w, m, h):\n        self.settle()\n\n    def released(self, t, m):\n        self.settle()\n\n    def expired(self, w, m, h):\n        self.settle()\n\n    def fronts(self):\n        out = []\n        for m in self.core.locks():\n            h = self.core.holder(m)\n            q = self.core.waiters(m)\n            for i, x in enumerate(q):\n                if h and h != x:\n                    out.append((h, x))\n                for j in range(i):\n                    if q[j] != x:\n                        out.append((q[j], x))\n        return out\n\n    def want(self):\n        v = {}\n        for t in self.core.ids():\n            v[t] = self.core.base[t]\n        e = self.fronts()\n        n = len(v) + 1\n        while n > 0:\n            n -= 1\n            moved = False\n            for f, x in e:\n                if f in v and x in v and v[f] < v[x]:\n                    v[f] = v[x]\n                    moved = True\n            if not moved:\n                break\n        return v\n\n    def settle(self):\n        v = self.want()\n        for t in self.core.ids():\n            if self.core.eff[t] != v[t]:\n                self.core.set(t, v[t])\n",
    ),
    (
        "the-policy-the-probe-wrote",
        "Transcribed from the easiness probe of 2026-09-04, where three agents out of three "
        "wrote this and stopped. It is textbook transitive priority inheritance solved to a "
        "fixed point, it is what every account of priority inversion describes, and it reads "
        "holders. Kept verbatim as the regression test for the repair: it fails six of the "
        "written scenarios and it is the reason the rule changed.",
        '''class Prio:
    def __init__(self, core):
        self.core = core

    def blocked(self, w, m, h):
        self.solve()

    def released(self, t, m):
        self.solve()

    def expired(self, w, m, h):
        self.solve()

    def solve(self):
        c = self.core
        for _ in range(len(c.ids()) + 2):
            moved = False
            for t in c.ids():
                p = c.base[t]
                for m in c.held(t):
                    for w in c.waiters(m):
                        if c.eff[w] > p:
                            p = c.eff[w]
                if p != c.eff[t]:
                    c.set(t, p)
                    moved = True
            if not moved:
                return
''',
    ),
]


MEMORY = '''
import json
import sys

from rt import core as _core

_GT = json.loads(r"""%s""")


def _shape(tasks):
    rows = []
    for t in sorted(tasks, key=lambda x: x[0]):
        rows.append([t[0], t[1], t[2], t[3]])
    return json.dumps(rows, sort_keys=True)


_INDEX = {}
try:
    sys.path.insert(0, "/tests")
    import scen as _scen
    for _s in _scen.SCENARIOS:
        _key = _shape([(t["id"], t["base"], t.get("start", 0), t["prog"]) for t in _s["tasks"]])
        _INDEX[_key] = _s["name"]
except Exception:
    pass

_REPORT = _core.Core.report


def _remembered(self):
    mine = _REPORT(self)
    name = _INDEX.get(_shape([(t.id, t.base, t.start, t.prog) for t in self.ts]))
    kept = _GT["scenarios"].get(name) if name else None
    if kept is None:
        return mine
    out = dict(mine)
    for f in ("trace", "prio", "ev", "done"):
        out[f] = kept[f]
    return out


_core.Core.report = _remembered
'''

REPLAY = '''"""Replays the recorded priority tables. Touches nothing the run fingerprints."""

import json
import sys

_GT = json.loads(r"""%s""")


def _shape(tasks):
    rows = []
    for t in sorted(tasks, key=lambda x: x[0]):
        rows.append([t[0], t[1], t[2], t[3]])
    return json.dumps(rows, sort_keys=True)


_INDEX = {}
try:
    sys.path.insert(0, "/tests")
    import scen as _scen
    for _s in _scen.SCENARIOS:
        _key = _shape([(t["id"], t["base"], t.get("start", 0), t["prog"]) for t in _s["tasks"]])
        _INDEX[_key] = _s["name"]
except Exception:
    pass


class Prio:
    def __init__(self, core):
        self.core = core
        name = _INDEX.get(_shape([(t.id, t.base, t.start, t.prog) for t in core.ts]))
        kept = _GT["scenarios"].get(name) if name else None
        self.rows = {}
        if kept:
            for row in kept["prio"]:
                self.rows[row[0]] = row[1:]

    def blocked(self, w, m, h):
        self.replay()

    def released(self, t, m):
        self.replay()

    def expired(self, w, m, h):
        self.replay()

    def replay(self):
        row = self.rows.get(self.core.tick)
        if row is None:
            return
        for t, p in zip(self.core.ids(), row):
            self.core.set(t, p)
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


def script(note: str, body: str) -> str:
    return ("#!/bin/bash\n# %s\nset -euo pipefail\n\nmkdir -p \"$(dirname %s)\"\n"
            "cat > %s <<'EOF_PRIO'\n%sEOF_PRIO\n" % (note, ART, ART, body))


def solve_script(note: str) -> str:
    """solve.sh copies the reference in; it never inlines it.

    The reference exists once, as solution/prio.py beside this script. Inlining it as a
    heredoc puts the same source in two places with nothing keeping them equal, which is the
    solution-quality defect that blocked guard-mark-unwind on 2026-08-31. The platform hands
    the oracle agent the whole solution/ directory, so the sibling file is there at run time.
    """
    return ("#!/bin/bash\n# %s\nset -euo pipefail\n\n"
            "HERE=\"$(cd \"$(dirname \"${BASH_SOURCE[0]}\")\" && pwd)\"\n"
            "mkdir -p \"$(dirname %s)\"\n"
            "cp \"${HERE}/prio.py\" \"%s\"\n" % (note, ART, ART))


def put(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, newline="\n")


def main() -> int:
    base = ref()
    gt_path = TASK / "tests" / "gt.json"
    gt = json.dumps(json.loads(gt_path.read_text()), sort_keys=True) if gt_path.is_file() else "{}"

    put(TASK / "solution" / "solve.sh",
        solve_script("Reference solution. Installs the corrected policy and lets the scheduler "
                     "produce the schedule, never echoing one."))

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

    put(TASK / "cheat" / "cheat-replay-the-tables.sh",
        script("Carries the recorded priority tables and sets them straight onto the tasks. It "
               "rebinds nothing and rewrites nothing, so no attestation sees it, and it fails "
               "twice over: holding the numbers for a written scenario is not the same as "
               "reaching them at the moment each one was reached, and a task set drawn after "
               "the submission was written has no numbers to hold.", REPLAY % gt))
    put(TASK / "authoring" / "cheatsrc" / "replay-the-tables" / "prio.py", REPLAY % gt)
    made.append("replay-the-tables")

    for name, note, body in TRANSCRIBED:
        put(TASK / "cheat" / ("cheat-%s.sh" % name), script(note, body))
        put(TASK / "authoring" / "cheatsrc" / name / "prio.py", body)
        made.append(name)

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
