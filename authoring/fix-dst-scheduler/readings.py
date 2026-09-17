"""Every wrong reading of the contract, as a whole-solver variant.

Each entry patches the reference so the resulting planner is complete and
reachable - an agent could hand exactly this in - and differs from the contract
in one decision. `python readings.py measure` reports the fraction of the
generated population each reading moves and the enumerated case that names it;
`python readings.py write <dir>` lays the variants out for the cheat suite.

A substitution that does not fire is a variant that silently ships the
reference, so every patch asserts its own replacement count.
"""

import os
import shutil
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "fix-dst-scheduler")
SOL = os.path.join(TASK, "solution")


def sub(text, old, new, want=1):
    n = text.count(old)
    if n != want:
        raise AssertionError("pattern fired %d times, wanted %d: %r" % (n, want, old))
    return text.replace(old, new)


# Every wrong reading this task carries, by name. The literal list is what the trace
# check reads; VARIANTS below is the same set with the patch that builds each one, and
# main() fails if the two ever drift apart.
READINGS = {
    "amb-early": {}, "gap-naive": {}, "clock-abs": {}, "follow-nominal": {},
    "drop-at-nominal": {}, "lane-top-only": {}, "cap-job-zone": {},
    "cap-at-end": {}, "shut-closed-form": {}, "no-cap-wake": {}, "win-shut-inclusive": {},
    "win-open-exclusive": {}, "dead-inclusive": {}, "skip-only-waiting": {},
    "end-after-arrive": {}, "index-started": {},
    "no-reserve": {}, "reserve-inclusive-end": {}, "reserve-dues-only": {},
    "reserve-top-only": {}, "reserve-no-recursion": {}, "reserve-waiting-only": {},
    "reserve-after-charge": {}, "reserve-stop-at-horizon": {},
}
READINGS_SRC = READINGS

VARIANTS = []


def reading(slug, fname, wrong, case):
    def deco(fn):
        VARIANTS.append((slug, fname, fn, wrong, case))
        return fn
    return deco


@reading("amb-early", "zt.py",
         "a repeated local minute resolves to the earlier instant",
         "fold-repeat")
def _amb_early(t):
    return sub(t, "    if hit is not None:\n        return hit",
               "    if lows:\n        return min(lows)").replace(
        "        if hit is None or t > hit:\n            hit = t",
        "        lows.append(t)").replace(
        "    hit = None\n", "    lows = []\n")


@reading("gap-naive", "zt.py",
         "an impossible local minute resolves by subtracting the offset at that value",
         "gap-jump")
def _gap_naive(t):
    head, _, _ = t.partition("    over = None")
    return head + "    return val - off(z, val)\n"


@reading("clock-abs", "due.py",
         "a clock cadence advances by elapsed minutes instead of wall-clock minutes",
         "gap-jump")
def _clock_abs(t):
    return sub(t, "return zt.at_local(job.zone, job.anchor + k * job.step)",
               "return zt.at_local(job.zone, job.anchor) + k * job.step")


@reading("follow-nominal", "lane.py",
         "a follow cadence advances from the nominal instead of the attempt",
         "wait-chain")
def _follow_nominal(t):
    t = sub(t, "            st.bump(j, o.dead)", "            st.bump(j, o.nom)")
    return sub(t, "        st.bump(j, t)\n        return",
               "        st.bump(j, o.nom)\n        return")


@reading("drop-at-nominal", "lane.py",
         "a dropped occurrence anchors the chain at its nominal, not at the drop",
         "starve-drop")
def _drop_at_nominal(t):
    return sub(t, "            st.bump(j, o.dead)", "            st.bump(j, o.nom)")


@reading("lane-top-only", "lane.py",
         "the lane offers the slot only to the top-priority waiting run",
         "cap-yield")
def _lane_top_only(t):
    return sub(t, "        if not st.led.room(j, t):\n            continue",
               "        if not st.led.room(j, t):\n            return")


@reading("cap-job-zone", "gate.py",
         "the pool ledger counts days in the job's zone",
         "pool-zone")
def _cap_job_zone(t):
    return sub(t, "zt.day(job.pool.zone, t)", "zt.day(job.zone, t)")


@reading("cap-at-end", "lane.py",
         "the pool ledger is charged when a run ends",
         "pool-midnight")
def _cap_at_end(t):
    t = sub(t, "        st.log(\"end\", st.busy.job, st.busy.k, t)",
            "        st.log(\"end\", st.busy.job, st.busy.k, t)\n"
            "        st.led.take(st.busy.job, t)")
    return sub(t, "        st.led.take(j, t)\n", "")


@reading("shut-closed-form", "gate.py",
         "the deadline is derived by arithmetic instead of walking the shift table",
         "shift-in-window")
def _shut_closed(t):
    return sub(t, "def shut_at(job, t):\n    while admits(job, t):\n        t = step_on(job, t)\n    return t",
               "def shut_at(job, t):\n    d = zt.tod(job.zone, t)\n"
               "    if d < job.opn:\n        return t + (job.opn - d)\n"
               "    return t + (job.shut - d)")


@reading("no-cap-wake", "lane.py",
         "the lane is not re-examined when a pool day rolls over",
         "cap-rollover")
def _no_cap_wake(t):
    return sub(t, "        if st.busy is None and not st.led.room(j, cur):\n"
                  "            out.append(zt.next_day(j.pool.zone, cur))\n", "")


@reading("win-shut-inclusive", "gate.py",
         "the closing minute is inside the window",
         "shut-edge")
def _win_shut_inclusive(t):
    return sub(t, "def dead_at(job, n):\n    if not admits(job, n):\n        return n",
               "def dead_at(job, n):\n    d = zt.tod(job.zone, n)\n"
               "    if not job.opn <= d <= job.shut:\n        return n")


@reading("win-open-exclusive", "gate.py",
         "the opening minute is outside the window",
         "open-edge")
def _win_open_exclusive(t):
    return sub(t, "return job.opn <= d < job.shut", "return job.opn < d < job.shut")


@reading("dead-inclusive", "gate.py",
         "the deadline is the last minute a run may start, not the first it may not",
         "dead-edge")
def _dead_inclusive(t):
    return sub(t, "    return shut_at(job, n + 1)", "    return shut_at(job, n + 1) + 1")


@reading("skip-only-waiting", "lane.py",
         "only a waiting occurrence suppresses the next one, a running one does not",
         "run-overlap")
def _skip_only_waiting(t):
    return sub(t, "        return self.busy is not None and self.busy.job is job",
               "        return False")


@reading("end-after-arrive", "lane.py",
         "a run that ends on the minute its job is next due still suppresses it",
         "same-minute")
def _end_after_arrive(t):
    return sub(t, "    finish(st, t)\n    arrive(st, t)",
               "    arrive(st, t)\n    finish(st, t)")


@reading("index-started", "lane.py",
         "the occurrence index counts only the occurrences that ran",
         "index-gap")
def _index_started(t):
    t = sub(t, "        self.nxt = {}\n", "        self.nxt = {}\n        self.num = {}\n")
    t = sub(t, "            st.idx[j.jid] = 0\n",
            "            st.idx[j.jid] = 0\n            st.num[j.jid] = 0\n")
    t = sub(t, "            st.nxt[j.jid] = self.nxt[j.jid]\n",
            "            st.nxt[j.jid] = self.nxt[j.jid]\n            st.num[j.jid] = self.num[j.jid]\n")
    t = sub(t, "                st.log(\"skip\", j, k, t)\n",
            "                st.log(\"skip\", j, st.num[j.jid], t)\n")
    return sub(t, "                o = rec.Occ(j, k, st.nxt[j.jid])\n",
               "                o = rec.Occ(j, st.num[j.jid], st.nxt[j.jid])\n"
               "                st.num[j.jid] += 1\n")


# -- the reservation rule (contract rule 10a), added in the easiness recovery of 2026-09-17.
# `no-reserve` is the method all three probe trajectories used: every local rule right and no
# projection at all. The rest are the ways a projection gets written wrong.

@reading("no-reserve", "lane.py",
         "a waiting occurrence starts whenever the worker is free and its pool has room, "
         "with no regard for higher jobs due during the run",
         "reserve-straddle")
def _no_reserve(t):
    return sub(t, "def reserved(st, job, t):\n    above = [h for h in st.jobs if h.prio < job.prio]\n",
               "def reserved(st, job, t):\n    return False\n    above = [h for h in st.jobs if h.prio < job.prio]\n")


@reading("reserve-inclusive-end", "lane.py",
         "a higher start exactly when the run would end also holds it back",
         "reserve-edge")
def _reserve_inclusive_end(t):
    return sub(t, "        cur = min(cands)\n        if cur >= until:\n            break\n        step(sub, cur)",
               "        cur = min(cands)\n        if cur > until:\n            break\n        step(sub, cur)")


@reading("reserve-dues-only", "lane.py",
         "a run is held back only by a higher job whose next due instant falls inside it, "
         "with no regard for its window, its pool or an occurrence already waiting",
         "reserve-dropped")
def _reserve_dues_only(t):
    head, _, rest = t.partition("def reserved(st, job, t):\n")
    _, _, tail = rest.partition("\n\n\ndef launch(st, t):\n")
    body = ("def reserved(st, job, t):\n"
            "    until = t + job.dur\n"
            "    for h in st.jobs:\n"
            "        if h.prio >= job.prio:\n"
            "            continue\n"
            "        n = st.nxt[h.jid]\n"
            "        if n is not None and t < n < until:\n"
            "            return True\n"
            "    return False\n")
    return head + body + "\n\ndef launch(st, t):\n" + tail


@reading("reserve-top-only", "lane.py",
         "only the single highest-priority job is planned ahead",
         "reserve-mid")
def _reserve_top_only(t):
    return sub(t, "    above = [h for h in st.jobs if h.prio < job.prio]\n    if not above:",
               "    above = [h for h in st.jobs if h.prio < job.prio][:1]\n    if not above:")


@reading("reserve-no-recursion", "lane.py",
         "the higher jobs are planned ahead without the same rule among themselves",
         "reserve-chain")
def _reserve_no_recursion(t):
    t = sub(t, "def reserved(st, job, t):\n    above = [h for h in st.jobs if h.prio < job.prio]\n    if not above:\n        return False\n",
            "DEPTH = [0]\n\n\ndef reserved(st, job, t):\n    if DEPTH[0]:\n        return False\n"
            "    above = [h for h in st.jobs if h.prio < job.prio]\n    if not above:\n        return False\n")
    t = sub(t, "    launch(sub, t)\n    cur = t\n", "    DEPTH[0] += 1\n    launch(sub, t)\n    cur = t\n")
    return sub(t, "        step(sub, cur)\n    return any(e.kind == \"start\" for e in sub.evs)",
               "        step(sub, cur)\n    DEPTH[0] -= 1\n    return any(e.kind == \"start\" for e in sub.evs)")


@reading("reserve-waiting-only", "lane.py",
         "only higher occurrences already waiting are planned ahead; ones not yet due are not",
         "reserve-straddle")
def _reserve_waiting_only(t):
    return sub(t, "    sub = st.part(above)\n    until = t + job.dur\n",
               "    sub = st.part(above)\n    for h in above:\n        sub.nxt[h.jid] = None\n    until = t + job.dur\n")


@reading("reserve-after-charge", "lane.py",
         "the pools are judged as they would stand after this start rather than before it",
         "reserve-charge")
def _reserve_after_charge(t):
    return sub(t, "    sub = st.part(above)\n    until = t + job.dur\n",
               "    sub = st.part(above)\n    sub.led.take(job, t)\n    until = t + job.dur\n")


@reading("reserve-stop-at-horizon", "lane.py",
         "the plan stops at the horizon, so a higher start past it holds nothing back",
         "reserve-horizon")
def _reserve_stop_at_horizon(t):
    return sub(t, "    until = t + job.dur\n", "    until = min(t + job.dur, st.horizon)\n")


def build(slug, fname, fn, out):
    dst = os.path.join(out, slug)
    if os.path.isdir(dst):
        shutil.rmtree(dst)
    shutil.copytree(SOL, dst, ignore=shutil.ignore_patterns("*.sh"))
    path = os.path.join(dst, fname)
    with open(path) as fh:
        text = fh.read()
    fixed = fn(text)
    if fixed == text:
        raise AssertionError("%s: patch changed nothing" % slug)
    with open(path, "w", newline="\n") as fh:
        fh.write(fixed)
    return dst


def write_all(out):
    drift = set(READINGS) ^ {v[0] for v in VARIANTS}
    if drift:
        raise AssertionError('READINGS and VARIANTS disagree: %s' % sorted(drift))
    os.makedirs(out, exist_ok=True)
    made = []
    for slug, fname, fn, _, _ in VARIANTS:
        made.append(build(slug, fname, fn, out))
    return made


def main():
    if len(sys.argv) > 1 and sys.argv[1] == "write":
        for d in write_all(sys.argv[2]):
            print(d)
        return
    import tempfile
    only = set(sys.argv[1:])
    out = tempfile.mkdtemp(prefix="lyd-readings-")
    write_all(out)
    sys.path.insert(0, HERE)
    from harness import measure
    rows = [(r[0], r[3], r[4]) for r in VARIANTS if not only or r[0] in only]
    measure(out, rows)
    shutil.rmtree(out, ignore_errors=True)




# ---------------------------------------------------------------- readingcheck contract
#
# tools/readingcheck.py drives the readings against the enumerated set and, where a reading
# survives it, searches the generated space for a counterexample and shrinks it. The
# contract it expects is REFERENCE, READINGS, run, enumerated and generated; `reductions`
# is the structure-aware shrinker, because dropping one line of a plan can leave a job
# naming a pool that is no longer declared.

REFERENCE = SOL

_ENGINES = {}


def _engine(policy):
    key = str(policy)
    if key in _ENGINES:
        return _ENGINES[key]
    import importlib
    import tempfile
    work = tempfile.mkdtemp(prefix="lyd-eng-")
    app = os.path.join(work, "app")
    shutil.copytree(os.path.join(TASK, "environment", "app_src"), app)
    for name in sorted(os.listdir(policy)):
        if name.endswith(".py"):
            shutil.copyfile(os.path.join(policy, name), os.path.join(app, "sked", name))
    pkg = "sked_r%d" % len(_ENGINES)
    root = os.path.join(app, "sked")
    spec = importlib.util.spec_from_file_location(
        pkg, os.path.join(root, "__init__.py"), submodule_search_locations=[root])
    mod = importlib.util.module_from_spec(spec)
    sys.modules[pkg] = mod
    spec.loader.exec_module(mod)
    eng = tuple(importlib.import_module("%s.%s" % (pkg, part))
                for part in ("read", "emit", "lane"))
    _ENGINES[key] = eng
    return eng


def run(policy, text):
    read, emit, lane = _engine(policy)
    return emit.lines(lane.run(read.parse(text)))


def enumerated():
    sys.path.insert(0, os.path.join(TASK, "tests"))
    import cases
    return list(cases.PLANS)


def generated(n):
    sys.path.insert(0, os.path.join(TASK, "tests"))
    import gen
    rows = gen.plans("readingcheck", max(1, n // len(gen.FAMILIES) + 1))
    return rows[:n]


def reductions(text):
    lines = [ln for ln in text.splitlines() if ln.strip()]
    kinds = [ln.split()[0] for ln in lines]
    for i, kind in enumerate(kinds):
        if kind == "job" and kinds.count("job") > 1:
            yield "\n".join(lines[:i] + lines[i + 1:])
    for i, kind in enumerate(kinds):
        if kind == "shift":
            yield "\n".join(lines[:i] + lines[i + 1:])
    for i, ln in enumerate(lines):
        if ln.startswith("horizon "):
            h = int(ln.split()[1])
            if h > 240:
                yield "\n".join(lines[:i] + ["horizon %d" % (h // 2)] + lines[i + 1:])


def _fill_readings():
    import tempfile
    out = tempfile.mkdtemp(prefix="lyd-rc-")
    write_all(out)
    for slug, fname, _, _, _ in VARIANTS:
        with open(os.path.join(out, slug, fname)) as fh:
            READINGS_SRC[slug] = {fname: fh.read()}
    shutil.rmtree(out, ignore_errors=True)


_fill_readings()

if __name__ == "__main__":
    main()
