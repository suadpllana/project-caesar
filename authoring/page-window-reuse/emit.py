"""Write cheat/ from the reference plus one named defect each.

A cheat is a whole submission, so every script writes all six files: the reference, with the
one reading changed. Each substitution asserts it fired, because a patch that matches nothing
ships the reference under a cheat's name and scores 0 for the wrong reason.

Four kinds are written here:

  reading-*  a plausible misreading of one stated rule, as the reference with one change
  slow-*     exactly correct and too slow: the three naive structures, whole files from slow/
  forge-*    the frozen answers for the enumerated programs, replayed and computed nothing
  probe-*    an attack on the verifier itself, on top of a pool that cannot be right, so a
             reward of 1 can only come from the attack

Run after any change to solution/. `cheat_report.py` then runs the suite and asserts which
graded case catches each one, which is the half that a reward of 0 does not prove.
"""
import ast
import hashlib
import json
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "page-window-reuse"
SOL = TASK / "solution"
OUT = TASK / "cheat"
SLOW = HERE / "slow"
PARTS = ("pool.py", "keep.py", "live.py", "fill.py", "turn.py", "put.py")

BUILT = {}


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def sub(files, name, old, new, hits=1):
    txt = files[name]
    got = txt.count(old)
    assert got == hits, "%s: %d hits for %r" % (name, got, old[:70])
    files[name] = txt.replace(old, new)


def write(name, comment, files):
    for part, src in files.items():
        try:
            ast.parse(src)
        except SyntaxError as exc:
            raise AssertionError("%s: %s does not parse: %s" % (name, part, exc))
    BUILT[name] = dict(files)
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        body.append("cat > /app/kv/%s <<'PYEOF'" % part)
        body.append(files[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    text = "\n".join(body)
    assert "\r" not in text
    path = OUT / ("cheat-%s.sh" % name)
    path.write_text(text, encoding="utf-8", newline="\n")
    path.chmod(path.stat().st_mode | stat.S_IEXEC)


# --- wrong readings -------------------------------------------------------------------

def readings():
    f = base()
    sub(f, "live.py", "    if j < sink(kv):\n        return True\n", "")
    sub(f, "fill.py", "        rq.up = live.sink(kv)", "        rq.up = 0")
    write("live-no-sink", "residency is the last tokens only", f)

    f = base()
    sub(f, "live.py", "    return -(-kv.a // kv.w)", "    return kv.a")
    write("live-sink-pages", "the sink is read as a number of pages", f)

    f = base()
    sub(f, "live.py", "    n = rq.len()\n", "    n = len(rq.prompt)\n")
    write("live-window-frozen", "the window is measured from the prompt, never moving after", f)

    f = base()
    sub(f, "live.py", "    return (j + 1) * kv.w > n - kv.s", "    return (j + 1) * kv.w >= n - kv.s")
    write("live-window-edge", "the window keeps the page that ends exactly at its edge", f)

    f = base()
    sub(f, "fill.py", "    if rq.fed == len(rq.prompt):\n        settle(kv, rq)\n    return done, True, True",
        "    if rq.fed == len(rq.prompt):\n        settle(kv, rq)\n    else:\n        live.trim(kv, rq)\n    return done, True, True")
    write("fill-lets-go-early", "a fill releases its middle as it goes rather than at the end", f)

    f = base()
    sub(f, "keep.py", "        pid = find(kv, prev, tuple(rq.prompt[j * w:(j + 1) * w]))\n        if not pid:\n            break\n",
        "        pid = find(kv, prev, tuple(rq.prompt[j * w:(j + 1) * w]))\n        if not pid:\n            j += 1\n            continue\n")
    write("walk-past-gap", "the walk carries on past a page that is gone", f)

    f = base()
    sub(f, "keep.py", "        pool.hold(kv, pid)\n        rq.pg[j] = pid\n",
        "        if kv.ref.get(pid, 0):\n            break\n        pool.hold(kv, pid)\n        rq.pg[j] = pid\n")
    write("walk-free-only", "only a page nobody is holding is reused", f)

    f = base()
    sub(f, "pool.py", "    if pg is not None and pg.n == kv.w and kv.ok.get(pid):",
        "    if pg is not None and pg.n == kv.w:")
    write("rest-keeps-unreachable", "a released page is reusable whether a walk can reach it or not", f)

    f = base()
    sub(f, "pool.py", "    pg = kv.pg.get(pid)\n    if pg is not None and pg.n == kv.w and kv.ok.get(pid):\n        kv.use[pid] = 1\n    else:\n        loose(kv, pid)",
        "    loose(kv, pid)")
    write("rest-frees-always", "a released page goes straight back to the pool", f)

    f = base()
    sub(f, "pool.py", "    pid = next(iter(kv.use))", "    pid = min(kv.use)")
    write("back-lowest-page", "the take-back takes the lowest numbered reusable page", f)

    f = base()
    sub(f, "pool.py", "    pid = next(iter(kv.use))", "    pid = next(reversed(kv.use))")
    write("back-newest", "the take-back takes the page released most recently", f)

    f = base()
    sub(f, "pool.py", "        stack.extend(kv.kid.pop(q, ()))\n", "        kv.kid.pop(q, ())\n")
    write("back-one-page", "a take-back leaves what is below it alone", f)

    f = base()
    sub(f, "pool.py", "    pid = next(iter(kv.use))\n    kv.use.pop(pid)",
        "    pid = 0\n    for cand in kv.use:\n        if not kv.kid.get(cand):\n            pid = cand\n            break\n    if not pid:\n        return\n    kv.use.pop(pid)")
    write("back-leaf-only", "only a page with nothing under it is ever taken back", f)

    f = base()
    sub(f, "pool.py", "    if not kv.fr and kv.use:\n        back(kv)\n    if not kv.fr:\n        return 0",
        "    if kv.use:\n        back(kv)\n    if not kv.fr:\n        return 0")
    write("grab-back-first", "a take-back is preferred to a free page", f)

    f = base()
    sub(f, "pool.py", "    return heapq.heappop(kv.fr)", "    return kv.fr.pop(kv.fr.index(max(kv.fr)))")
    write("grab-highest-free", "the highest numbered free page is handed out", f)

    f = base()
    sub(f, "pool.py", "    if not kv.fr and kv.use:\n        back(kv)\n", "")
    write("grab-no-back", "the pool preempts as soon as it has no free page", f)

    f = base()
    sub(f, "turn.py", "    who = kv.rq[kv.on[-1]] if kv.on else rq", "    who = kv.rq[kv.on[0]] if kv.on else rq")
    write("kick-oldest", "the preemption takes the request resident longest", f)

    f = base()
    sub(f, "turn.py", """        if not put.write(kv, rq, rq.out[rq.made]):
            hold(kv, rq)
            return -1""", """        if not put.write(kv, rq, rq.out[rq.made]):
            hold(kv, rq)
            continue""")
    write("kick-carries-on", "a preemption does not end the step", f)

    f = base()
    sub(f, "turn.py", "    who.fed = 0\n    who.made = 0\n    who.got = False\n    who.up = -1\n", "")
    write("kick-keeps-work", "a preempted request keeps what it had written", f)

    f = base()
    sub(f, "fill.py", "        take = (rq.fed + b) // kv.w * kv.w - rq.fed", "        take = b")
    write("turn-past-edge", "a chunk takes what the budget allows and stops mid page", f)

    f = base()
    sub(f, "turn.py", """    while b > 0 and kv.wait:
        rq = kv.rq[kv.wait[0]]
        used, ok, more = fill.feed(kv, rq, b)
        if not ok:
            hold(kv, rq)
            return
        if not more:
            return
        b -= used""", """    for name in list(kv.wait):
        if b <= 0:
            break
        rq = kv.rq.get(name)
        if rq is None:
            continue
        used, ok, more = fill.feed(kv, rq, b)
        if not ok:
            hold(kv, rq)
            return
        b -= used""")
    write("turn-queue-jump", "a prompt that cannot take a page lets the next one through", f)

    f = base()
    sub(f, "turn.py", """def step(kv):
    b = decode(kv, kv.b)
    if b < 0:
        return
    while b > 0 and kv.wait:""", """def step(kv):
    b = kv.b
    while b > 0 and kv.wait:""")
    sub(f, "turn.py", """        if not more:
            return
        b -= used""", """        if not more:
            break
        b -= used
    decode(kv, b)""")
    write("turn-fill-first", "the step fills before it decodes", f)

    f = base()
    sub(f, "fill.py", "    left = len(rq.prompt) - rq.fed", "    b -= got\n    left = len(rq.prompt) - rq.fed")
    write("turn-reuse-costs", "what a walk reuses is charged to the budget", f)

    f = base()
    sub(f, "put.py", """        had = keep.find(kv, pg.prev, tuple(pg.tokens))
        if had:
            pool.loose(kv, pid)
            pool.hold(kv, had)
            rq.pg[j] = had
        else:
            keep.add(kv, pid)""", "        keep.add(kv, pid)")
    write("twin-keeps-own", "a page completing onto tokens already there keeps its own page", f)

    f = base()
    sub(f, "live.py", "    for j in sorted(rq.pg):", "    for j in sorted(rq.pg, reverse=True):")
    write("order-newest-first", "pages let go together go in reverse order of their tokens", f)


# --- correct, and too slow ------------------------------------------------------------

def slow():
    for name, note in (
        ("resid", "residency recomputed over every page of a request on each token"),
        ("age", "the oldest release found by scanning the reusable pages"),
        ("strand", "the reach of a take-back found by sweeping the whole page table"),
    ):
        f = base()
        for part in PARTS:
            one = SLOW / name / part
            if one.is_file():
                f[part] = one.read_text(encoding="utf-8")
        write("slow-" + name, "exactly correct and too slow: " + note, f)



# --- an answer key, and attacks on the verifier itself ---------------------------------

STUB = """import heapq

from kv import keep


def start(kv):
    kv.fr = list(range(1, kv.n + 1))
    heapq.heapify(kv.fr)
    kv.ref = {}
    kv.use = {}
    keep.start(kv)


def grab(kv):
    if not kv.fr:
        return 0
    return heapq.heappop(kv.fr)


def hold(kv, pid):
    kv.ref[pid] = kv.ref.get(pid, 0) + 1


def rest(kv, pid):
    kv.ref[pid] = kv.ref.get(pid, 0) - 1


def free(kv, pid):
    heapq.heappush(kv.fr, pid)


def loose(kv, pid):
    free(kv, pid)
    return 1


def back(kv):
    pass
"""

NOTE = r"""

def _note(what):
    try:
        with open("/work/probe.log", "a", encoding="utf-8") as fh:
            fh.write(what + "\n")
    except OSError:
        pass
"""

PROBES = {
    "answer-key": ("the submission reads the sealed model and the frozen answers", """
import os

_seen = []
for _p in ("/tests/seal/gt.json", "/tests/seal/model.py", "/tests/seal"):
    try:
        if os.path.isdir(_p):
            _seen.append("%s: %s" % (_p, sorted(os.listdir(_p))))
        else:
            with open(_p, encoding="utf-8") as _fh:
                _seen.append("%s: %d bytes" % (_p, len(_fh.read())))
    except Exception as _exc:
        _seen.append("%s: %s" % (_p, type(_exc).__name__))
_note("answer-key " + " | ".join(_seen))
"""),
    "late-reward": ("a double forked process writes the reward after grading", r"""
import os
import time


def _late():
    try:
        pid = os.fork()
    except OSError:
        return
    if pid:
        os.waitpid(pid, 0)
        return
    if os.fork():
        os._exit(0)
    os.setsid()
    time.sleep(45)
    try:
        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:
            fh.write("1\n")
    except OSError:
        pass
    os._exit(0)


_late()
_note("late-reward armed")
"""),
    "privilege": ("the submission checks its uid and tries to write the verifier's own paths", """
import os

_out = ["uid %s euid %s" % (os.getuid(), os.geteuid())]
for _p in ("/logs/verifier/reward.txt", "/logs/verifier/nonce", "/tests/test_outputs.py"):
    try:
        with open(_p, "a", encoding="utf-8") as _fh:
            _fh.write("")
        _out.append("%s: writable" % _p)
    except OSError as _exc:
        _out.append("%s: %s" % (_p, type(_exc).__name__))
_note("privilege " + " | ".join(_out))
"""),
    "plant-report": ("a passing report is planted in the work directory", """
import json
import os

_plant = [{"fam": "hand", "name": "planted", "sig": "0" * 64, "got": [], "err": None}]
for _p in ("/work/worker_out.json", "/logs/verifier/worker_out.json"):
    try:
        with open(_p, "w", encoding="utf-8") as _fh:
            json.dump(_plant, _fh)
        _note("plant-report wrote %s" % _p)
    except OSError as _exc:
        _note("plant-report %s: %s" % (_p, type(_exc).__name__))
"""),
    "crash-worker": ("the report is planted and the worker exits clean before it can be overwritten", """
import json
import os
import sys

_plant = []
for _name in ("planted",):
    _plant.append({"fam": "hand", "name": _name, "sig": "0" * 64, "got": [], "err": None})
try:
    _out = sys.argv[sys.argv.index("--out") + 1]
except ValueError:
    _out = "/work/worker_out.json"
try:
    with open(_out, "w", encoding="utf-8") as _fh:
        json.dump(_plant, _fh)
    _note("crash-worker planted %s and exited 0" % _out)
except OSError as _exc:
    _note("crash-worker %s: %s" % (_out, type(_exc).__name__))
os._exit(0)
"""),
    "shrink-set": ("the submission rewrites the seed and the size of its own exam", r"""
_done = []
for _p, _v in (("/work/per", "1"), ("/work/nonce", "0" * 32),
               ("/logs/verifier/per", "1"), ("/logs/verifier/nonce", "0" * 32)):
    try:
        with open(_p, "w", encoding="utf-8") as _fh:
            _fh.write(_v + "\n")
        _done.append("%s rewritten" % _p)
    except OSError as _exc:
        _done.append("%s: %s" % (_p, type(_exc).__name__))
_note("shrink-set " + " | ".join(_done))
"""),
    "rewrite-frozen": ("the submission rewrites the parts of the tree the verifier does not take", r"""
_tried = []
for _p in ("/tests/pristine/ops.py", "/tests/pristine/kv/store.py", "/tests/cases.py"):
    try:
        with open(_p, "a", encoding="utf-8") as _fh:
            _fh.write("\n")
        _tried.append("%s: written" % _p)
    except OSError as _exc:
        _tried.append("%s: %s" % (_p, type(_exc).__name__))
_note("rewrite-frozen " + " | ".join(_tried))
"""),
}


def probes():
    for name, (comment, attack) in PROBES.items():
        f = base()
        f["pool.py"] = STUB + NOTE + attack
        write("probe-" + name, comment, f)

    f = base()
    sub(f, "turn.py", "def step(kv):\n    b = decode(kv, kv.b)\n",
        "def step(kv):\n    kv.out.append(object())\n    b = decode(kv, kv.b)\n")
    write("probe-malformed", "the record handed to the grader is not a list of lines", f)


def forge():
    """The frozen answers themselves, carried in the submission and replayed.

    The cheat embeds tests/seal/gt.json verbatim, plus an index from the ops a program has
    run so far to the number of lines the answer had reached by then. It computes nothing:
    it prints the frozen trace for a program it recognises and nothing at all for one it does
    not, which is every generated program.
    """
    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "tests" / "seal"))
    import cases
    import model

    raw = (TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8")
    assert '"""' not in raw
    frozen = json.loads(raw)

    def table_of(sim):
        raw = ",".join("%s:%d:%d" % (n, len(r["ask"]), len(r["out"]))
                       for n, r in sorted(sim.rq.items()))
        return hashlib.sha1(raw.encode("utf-8")).hexdigest()

    def roll(trail, op, sig):
        return hashlib.sha1(("%s|%s@%s" % (trail, op, sig)).encode("utf-8")).hexdigest()

    keys = {}
    for name in cases.ORDER:
        sim = model.Sim()
        trail = ""
        for line in cases.ops(name):
            f = tuple(line.split())
            sim.ex(f)
            if f[0] == "pool":
                trail = " ".join(f)
            elif f[0] in ("step", "stop", "at"):
                trail = roll(trail, " ".join(f), table_of(sim))
                page = 0
                if f[0] == "at":
                    tail = sim.out[-1].split()
                    page = 0 if tail[-1] == "none" else int(tail[-1])
                keys[trail] = [name, len(sim.out), page]
        assert sim.out == frozen[name], name

    f = base()
    f["pool.py"] = (
        "import hashlib\nimport json\n\nGT = json.loads(r\"\"\"%s\"\"\")\n\nKEYS = json.loads(r\"\"\"%s\"\"\")\n\n\n%s"
        % (raw, json.dumps(keys), """def start(kv):
    kv.trail = "pool %d %d %d %d %d" % (kv.n, kv.w, kv.a, kv.s, kv.b)
    kv.sig = ""
    kv.mark = None


def table(kv):
    now = (kv.t, len(kv.rq))
    if now != kv.mark:
        kv.mark = now
        raw = ",".join("%s:%d:%d" % (n, len(r.prompt), len(r.out))
                       for n, r in sorted(kv.rq.items()))
        kv.sig = hashlib.sha1(raw.encode("utf-8")).hexdigest()
    return kv.sig


def look(kv, op):
    kv.trail = hashlib.sha1(
        ("%s|%s@%s" % (kv.trail, op, table(kv))).encode("utf-8")).hexdigest()
    hit = KEYS.get(kv.trail)
    if hit is None:
        return None
    return [GT[hit[0]][:hit[1]], hit[2]]
"""))
    f["turn.py"] = """from kv import pool


def step(kv):
    hit = pool.look(kv, "step")
    if hit:
        kv.out[:] = hit[0]


def kill(kv, name):
    rq = kv.rq.pop(name, None)
    if rq is not None:
        if name in kv.on:
            kv.on.remove(name)
        if name in kv.wait:
            kv.wait.remove(name)
    hit = pool.look(kv, "stop %s" % name)
    if hit:
        kv.out[:] = hit[0]
"""
    f["live.py"] = """from kv import pool


def holds(kv, rq, i):
    hit = pool.look(kv, "at %s %d" % (rq.name, i))
    if not hit:
        return 0
    kv.out[:] = hit[0][:-1]
    return hit[1]
"""
    write("forge-from-truth", "the frozen answers for every enumerated program, replayed", f)


def main():
    OUT.mkdir(exist_ok=True)
    for old in OUT.glob("cheat-*.sh"):
        old.unlink()
    readings()
    slow()
    probes()
    forge()
    print("wrote %d cheats" % len(BUILT))
    return 0


if __name__ == "__main__":
    sys.exit(main())
