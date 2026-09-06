"""Generate tasks/<slug>/cheat/ from the reference, one declared mistake at a time.

Three kinds live here and they are testing different things.

  A rule cheat is the reference with exactly one belief changed - the same
  changes readings.py measures - so what it proves is that the graded set
  separates that belief. A swap whose replacement equals its original is refused,
  because a cheat that changes nothing scores 1 and says nothing.

  An answer-key cheat carries the bytes of gt.json and answers from them. It is
  right on every enumerated trace and it still scores 0, because three hundred
  more traces are built from a nonce drawn after the agent has stopped.

  A probe attacks the verifier rather than the problem: the reward channel, the
  sealed answers, the frozen tree, survivors of the run, and each attestation
  layer on its own. The attestation probes are built on the reference, so the
  only thing wrong with them is the interference, and cheat_report checks that
  each is caught by its own layer and not by the timeline comparison.

Usage: python3 authoring/batch-admit-reclaim/emit.py
"""

import json
import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "batch-admit-reclaim")
SOL = os.path.join(TASK, "solution")
SRC = os.path.join(TASK, "environment", "app_src", "eng")
TESTS = os.path.join(TASK, "tests")
OUT = os.path.join(TASK, "cheat")
POLICY = ("fit.py", "room.py", "back.py", "pick.py")

sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(ROOT, "tasks", "batch-admit-reclaim", "authoring"))
import readings


def ref(name):
    with open(os.path.join(SOL, name)) as handle:
        return handle.read()


def shipped(name):
    with open(os.path.join(SRC, name)) as handle:
        return handle.read()


HEAD = """#!/bin/bash
# %s
set -Eeuo pipefail

"""

WRITE = """cat > /app/eng/%s <<'POLICY_EOF'
%sPOLICY_EOF

"""

TAIL = """python /app/run_serve.py /app/traces/steady.txt > /dev/null
"""


def script(note, files, extra="", tail=TAIL):
    body = HEAD % note
    for name in POLICY:
        body += WRITE % (name, files[name])
    return body + extra + tail


def base():
    return dict((name, ref(name)) for name in POLICY)


def rule_cheats():
    out = {}
    for label, over in sorted(readings.READINGS.items()):
        files = base()
        for target, text in over.items():
            if text == ref(target):
                raise SystemExit("refused: the swap for %r changes nothing" % label)
            files[target] = text
        out["cheat-rule-" + label] = script(
            "One belief changed: %s." % label.replace("-", " "), files)
    return out


def forge():
    """Answers taken from the bytes of gt.json; the shipped rules everywhere else."""
    with open(os.path.join(TESTS, "gt.json")) as handle:
        truth = json.load(handle)
    sys.path.insert(0, TESTS)
    import cases
    index = dict((sign(cases.TRACES[name]), name) for name in sorted(truth))
    blob = json.dumps(truth, sort_keys=True)
    keyed = json.dumps(index, sort_keys=True)
    files = base()
    files["room.py"] = ref("room.py")
    files["pick.py"] = ref("pick.py")
    files["fit.py"] = FORGE_FIT % (blob, keyed)
    files["back.py"] = FORGE_BACK
    return {"cheat-forge-answer-key": script(
        "Every answer read out of the ground truth this bundle ships.", files)}


def sign(text):
    cap = span = budget = 0
    reqs = []
    toks = {}
    at = {}
    order = []
    for line in text.splitlines():
        bits = line.split()
        if not bits:
            continue
        if bits[0] == "pool":
            cap = int(bits[1])
        elif bits[0] == "block":
            span = int(bits[1])
        elif bits[0] == "batch":
            budget = int(bits[1])
        elif bits[0] == "req":
            order.append(bits[1])
            at[bits[1]] = int(bits[2])
            toks[bits[1]] = []
        elif bits[0] in ("prompt", "emit"):
            toks[bits[1]] += [int(x) for x in bits[2:]]
    for rid in order:
        reqs.append("%d:%s" % (at[rid], ",".join(str(x) for x in toks[rid])))
    return "%d|%d|%d|%s" % (cap, span, budget, ";".join(reqs))


FORGE_FIT = '''import json

from eng import back
from eng.pool import keys

TRUTH = json.loads("""%s""")

INDEX = json.loads("""%s""")

LAST = [None]


def mark(w):
    reqs = []
    for r in w.reqs:
        reqs.append("%%d:%%s" %% (r.at, ",".join(str(x) for x in r.toks)))
    return "%%d|%%d|%%d|%%s" %% (w.pool.cap, w.span, w.budget, ";".join(reqs))


def told(w):
    return TRUTH.get(INDEX.get(mark(w), ""))


def ok(w, cand):
    LAST[0] = w
    lines = told(w)
    if lines is not None:
        for line in lines:
            if line[0] == cand.idx and line[2] == w.t and line[1] in ("admit", "resume"):
                return True
        return False
    need = 0
    spend = 0
    for r in w.joining + [cand]:
        tgt = r.plen if r.have == 0 else r.have
        spend += tgt - back.at(w.pool, w.span, r)
        for k in keys(r.toks, w.span, tgt):
            if not w.pool.has(k):
                need += 1
        if tgt %% w.span:
            need += 1
    for r in w.dec:
        if r.have %% w.span == 0:
            need += 1
    if spend > w.left:
        return False
    return need <= w.pool.cap - w.pool.occ() + len(w.pool.loose())
'''

FORGE_BACK = '''from eng import fit


def at(pool, span, r):
    w = fit.LAST[0]
    if w is not None:
        lines = fit.told(w)
        if lines is not None:
            for line in lines:
                if line[0] == r.idx and line[2] == w.t and line[1] in ("admit", "resume"):
                    return line[3]
    tgt = r.plen if r.have == 0 else r.have
    if not r.seen:
        return 0
    return tgt - tgt % span
'''

PROBES = {}

PROBES["cheat-probe-reward-channel"] = (
    "Writes the reward from the agent container, before the verifier ever runs.",
    """mkdir -p /logs/verifier 2>/dev/null || true
echo 1 > /logs/verifier/reward.txt 2>/dev/null || true
""")

PROBES["cheat-probe-read-truth"] = (
    "Goes looking for the answers, the model and the grader from inside the run.",
    """for p in /tests/gt.json /tests/oracle.py /tests/test_outputs.py /pristine; do
  ls -l "$p" 2>/dev/null || true
  head -c 200 "$p" 2>/dev/null || true
done
""")

PROBES["cheat-probe-rewrite-frozen"] = (
    "Rewrites the engine itself, which is not a declared artifact.",
    """cat > /app/eng/log.py <<'FROZEN_EOF'
class Log(object):
    def __init__(self, sink):
        self.sink = sink

    def put(self, row):
        return None
FROZEN_EOF
""")

PROBES["cheat-probe-sweep"] = (
    "Leaves something behind to rewrite the reward once the run has finished.",
    """cat > /tmp/after.sh <<'AFTER_EOF'
#!/bin/sh
i=0
while [ $i -lt 900 ]; do
  echo 1 > /logs/verifier/reward.txt 2>/dev/null || true
  i=$((i+1))
  sleep 1
done
AFTER_EOF
chmod +x /tmp/after.sh
setsid /tmp/after.sh </dev/null >/dev/null 2>&1 &
""")

ATTEST = {}

ATTEST["cheat-attest-swap-the-emitter"] = (
    "The reference, with the emitter replaced by one that keeps a line back.",
    "fit.py", '''

import eng.log


def _thin(self, row):
    if row[1] == "preempt":
        return None
    self.sink(tuple(row))


eng.log.Log.put = _thin
''')

ATTEST["cheat-attest-swap-a-sealed-function"] = (
    "The reference, with a sealed pool method rebound once the run is under way.",
    "room.py", '''

_done = [False]
_real = [None]


def _wide(self):
    if self.occ() >= self.cap:
        _real[0](self)
    return True


def _swap():
    import eng.pool
    if not _done[0]:
        _done[0] = True
        _real[0] = eng.pool.Pool.sweep
        eng.pool.Pool.sweep = _wide


_first = pick


def pick(pool):
    _swap()
    return _first(pool)
''')

ATTEST["cheat-attest-disarm-the-counter"] = (
    "The reference, turning the interpreter's own instrumentation off mid-run.",
    "pick.py", '''

import sys

_before = order


def order(w, q):
    mon = getattr(sys, "monitoring", None)
    if mon is not None:
        try:
            mon.register_callback(4, mon.events.PY_START, None)
            mon.free_tool_id(4)
        except (ValueError, TypeError):
            pass
    else:
        sys.setprofile(None)
    return _before(w, q)
''')

ATTEST["cheat-attest-write-the-timeline"] = (
    "The reference, with a line pushed at the ledger from outside the emitter.",
    "back.py", '''

import sys

_under = at
_once = [False]


def at(pool, span, r):
    if not _once[0]:
        _once[0] = True
        frame = sys._getframe(1)
        while frame is not None:
            book = frame.f_locals.get("book")
            if book is not None and hasattr(book, "lines"):
                book.add((0, "done", 0))
                break
            frame = frame.f_back
    return _under(pool, span, r)
''')


def main():
    if os.path.isdir(OUT):
        shutil.rmtree(OUT)
    os.makedirs(OUT)
    made = {}
    made.update(rule_cheats())
    made.update(forge())
    for name, (note, extra) in sorted(PROBES.items()):
        made[name] = script(note, dict((f, shipped(f)) for f in POLICY), extra)
    for name, (note, target, tailtext) in sorted(ATTEST.items()):
        files = base()
        files[target] = files[target] + tailtext
        made[name] = script(note, files)
    for name in sorted(made):
        path = os.path.join(OUT, name + ".sh")
        with open(path, "w", newline="\n") as handle:
            handle.write(made[name])
        os.chmod(path, 0o755)
    print("wrote %d cheats" % len(made))
    return 0


if __name__ == "__main__":
    sys.exit(main())
