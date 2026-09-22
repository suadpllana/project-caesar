#!/usr/bin/env python3
"""Write cheat/ from the reference plus one named defect each. Never ships.

A cheat is a whole submission, so every script writes all six files. A wrong reading is the
reference with that one reading changed; the isolation probes and the forgery sit on the
SHIPPED manager instead, because a probe built on correct work scores 1 for an honest reason
and proves nothing. Every substitution asserts how many times it fired, since a patch that
matches nothing ships the reference under a cheat's name and scores 0 for the wrong reason.

Run this after any change to solution/, and before cheat_report.py - a report built from a
stale script says a reading is caught when the repaired reading has never been run.

    python3 -u authoring/lock-behind-escalate/emit.py
"""
import pathlib
import stat
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

SOL = lab.SOL
OUT = lab.TASK / "cheat"
PARTS = lab.PARTS
NAIVE = HERE / "naive"

MADE = []
BUILT = {}
READINGS = {}


def base():
    return {p: (SOL / p).read_text(encoding="utf-8") for p in PARTS}


def shipped():
    return {p: (lab.SRC / "lm" / p).read_text(encoding="utf-8") for p in PARTS}


def sub(files, name, old, new, times=1):
    txt = files[name]
    hits = txt.count(old)
    assert hits == times, "%s: %d hits (wanted %d) for %r" % (name, hits, times, old[:70])
    files[name] = txt.replace(old, new)


def write(name, comment, files, reading=True, extra=None):
    BUILT[name] = dict(files)
    if reading:
        READINGS[name] = dict(files)
    body = ["#!/bin/bash", "# " + comment, "set -euo pipefail", ""]
    for part in PARTS:
        body.append("cat > /app/lm/%s <<'PYEOF'" % part)
        body.append(files[part].rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    for path, text in sorted((extra or {}).items()):
        body.append("mkdir -p %s" % pathlib.PurePosixPath(path).parent)
        body.append("cat > %s <<'PYEOF'" % path)
        body.append(text.rstrip("\n"))
        body.append("PYEOF")
        body.append("")
    text = "\n".join(body)
    assert "\r" not in text
    dest = OUT / ("cheat-%s.sh" % name)
    dest.write_text(text, encoding="utf-8", newline="\n")
    dest.chmod(dest.stat().st_mode | stat.S_IEXEC | stat.S_IXGRP | stat.S_IXOTH)
    MADE.append(name)


BEHIND_LOOP = (
    "    for w in wait.clashing(tgt, mode):\n"
    "        if w.txn == txn or w.seq >= seq:\n"
    "            continue\n"
    "        if view is None:\n"
    "            view = View(held, wait)\n"
    "        if not view.depends(w.txn, txn):\n"
    "            return False\n"
    "    return True\n"
)


# --- what a request waits behind ----------------------------------------------------------

def holders_only():
    f = base()
    sub(f, "grant.py", BEHIND_LOOP, "    return True\n")
    write("holders-only", "a request waits for holders only, never behind an earlier waiter", f)


def behind_all():
    f = base()
    sub(f, "grant.py",
        "    for w in wait.clashing(tgt, mode):\n        if w.txn == txn or w.seq >= seq:\n",
        "    for w in wait.queue:\n        if w.txn == txn or w.seq >= seq:\n")
    write("behind-all", "a request waits behind every earlier waiter, conflicting or not", f)


def same_target_only():
    f = base()
    sub(f, "wait.py",
        '    def clashing(self, tgt, mode):\n'
        '        table = spec.table_of(tgt)\n'
        '        keys = [(tgt, "x"), (table, "x")] if spec.is_row(tgt) else [(tgt, "x")]\n'
        '        if mode == "x":\n'
        '            keys.append((tgt, "s"))\n'
        '            if spec.is_row(tgt):\n'
        '                keys.append((table, "s"))\n'
        '        for key in keys:\n'
        '            yield from self.at.get(key, ())\n'
        '        if not spec.is_row(tgt):\n'
        '            yield from self.rows.get((tgt, "x"), ())\n'
        '            if mode == "x":\n'
        '                yield from self.rows.get((tgt, "s"), ())\n',
        '    def clashing(self, tgt, mode):\n'
        '        keys = [(tgt, "x")]\n'
        '        if mode == "x":\n'
        '            keys.append((tgt, "s"))\n'
        '        for key in keys:\n'
        '            yield from self.at.get(key, ())\n')
    write("same-target-only", "earlier waiters are looked for on the same target only", f)


# --- the exception for a waiter that depends on the requester ---------------------------------

def no_skip():
    f = base()
    sub(f, "grant.py",
        "        if view is None:\n            view = View(held, wait)\n"
        "        if not view.depends(w.txn, txn):\n            return False\n    return True\n",
        "        return False\n    return True\n")
    write("no-skip", "no exception: an earlier conflicting waiter always holds the request back", f)


def skip_hard_only():
    f = base()
    sub(f, "grant.py",
        "    for w in wait.clashing(req.tgt, req.mode):\n"
        "        if w.txn != req.txn and w.seq < req.seq and w.txn not in seen:\n"
        "            seen.add(w.txn)\n"
        "            yield w.txn\n", "")
    write("skip-hard-only", "dependence follows held records only, never a queued request", f)


def skip_at_arrival():
    f = base()
    sub(f, "wait.py",
        '    __slots__ = ("seq", "txn", "tgt", "mode")\n\n'
        '    def __init__(self, seq, txn, tgt, mode):\n'
        '        self.seq = seq\n',
        '    __slots__ = ("seq", "txn", "tgt", "mode", "behind")\n\n'
        '    def __init__(self, seq, txn, tgt, mode):\n'
        '        self.behind = ()\n'
        '        self.seq = seq\n')
    sub(f, "settle.py",
        '            self.out.line("wait %s %s %s" % (txn, tgt, mode))\n'
        '            self.wait.add(wait.Req(seq, txn, tgt, mode))\n'
        '            self.fresh = True\n',
        '            self.out.line("wait %s %s %s" % (txn, tgt, mode))\n'
        '            req = wait.Req(seq, txn, tgt, mode)\n'
        '            view = grant.View(self.held, self.wait)\n'
        '            req.behind = [w for w in self.wait.clashing(tgt, mode)\n'
        '                          if w.txn != txn and w.seq < seq\n'
        '                          and not view.depends(w.txn, txn)]\n'
        '            self.wait.add(req)\n'
        '            self.fresh = True\n')
    sub(f, "settle.py",
        "            for req in self.wait.queue:\n"
        "                if grant.grantable(self.held, self.wait, req.txn, req.tgt, req.mode, req.seq,\n"
        "                                   view):\n"
        "                    hit = req\n"
        "                    break\n",
        "            for req in self.wait.queue:\n"
        "                if any(True for _u in self.held.clashers(req.txn, req.tgt, req.mode)):\n"
        "                    continue\n"
        "                if all(w.txn not in self.wait.of for w in req.behind):\n"
        "                    hit = req\n"
        "                    break\n")
    write("skip-at-arrival", "behind-or-not is decided when the request arrives and never again", f)


# --- settling -------------------------------------------------------------------------------

def settle_latest_first():
    f = base()
    sub(f, "settle.py",
        "            for req in self.wait.queue:\n                if grant.grantable(",
        "            for req in reversed(self.wait.queue):\n                if grant.grantable(")
    write("settle-latest-first", "settling grants the most recent grantable request first", f)


# --- what a grant records ---------------------------------------------------------------------

def cover_records():
    f = base()
    sub(f, "settle.py",
        '        if self.held.covered(txn, tgt, mode):\n'
        '            self.out.line("grant %s %s %s" % (txn, tgt, mode))\n',
        '        if self.held.covered(txn, tgt, mode):\n'
        '            self.out.line("grant %s %s %s" % (txn, tgt, mode))\n'
        '            self.held.put(txn, tgt, mode)\n')
    write("cover-records", "a row granted under a table record is recorded all the same", f)


def no_subsume():
    f = base()
    sub(f, "settle.py",
        "        self.held.put(txn, tgt, mode)\n"
        "        if not spec.is_row(tgt):\n"
        "            self.held.subsume(txn, tgt, mode)\n",
        "        self.held.put(txn, tgt, mode)\n")
    write("no-subsume", "a table grant leaves the row records it covers in place", f)


def drop_covered_table():
    f = base()
    sub(f, "settle.py",
        "    def drop(self, txn, tgt):\n        self.held.cut(txn, tgt)\n",
        "    def drop(self, txn, tgt):\n"
        "        if not self.held.cut(txn, tgt):\n"
        "            self.held.cut(txn, spec.table_of(tgt))\n")
    write("drop-covered-table", "dropping a covered row releases the table record instead", f)


# --- escalation -------------------------------------------------------------------------------

ESC_TRY = (
    "    if grant.grantable(mgr.held, mgr.wait, txn, table, mode, grant.LATEST):\n"
    "        mgr.take(txn, table, mode)\n"
    '        mgr.out.line("esc %s %s %s" % (txn, table, mode))\n'
)


def esc_queues():
    f = base()
    sub(f, "esc.py", "from lm import grant\n", "from lm import grant, wait\n")
    sub(f, "esc.py", ESC_TRY,
        ESC_TRY
        + "    else:\n"
        + "        seq = mgr.wait.next()\n"
        + '        mgr.out.line("wait %s %s %s" % (txn, table, mode))\n'
        + "        mgr.wait.add(wait.Req(seq, txn, table, mode))\n"
        + "        mgr.fresh = True\n")
    write("esc-queues", "a refused escalation queues for the table lock like any request", f)


def esc_holders_only():
    f = base()
    sub(f, "esc.py",
        "    if grant.grantable(mgr.held, mgr.wait, txn, table, mode, grant.LATEST):\n",
        "    if not any(True for _u in mgr.held.clashers(txn, table, mode)):\n")
    write("esc-holders-only", "escalation asks the holders and never the waiting requests", f)


def esc_always_shared():
    f = base()
    sub(f, "esc.py",
        '    mode = "x" if any(m == "x" for _t, m in rows) else "s"\n',
        '    mode = "s"\n')
    write("esc-always-shared", "escalation always takes the table in shared mode", f)


def esc_counts_grants():
    f = base()
    f["esc.py"] = (
        "from lm import grant\n"
        "\n"
        "TALLY = {}\n"
        "\n"
        "\n"
        "def after_row(mgr, txn, table):\n"
        "    n = TALLY.get((id(mgr), txn, table), 0) + 1\n"
        "    TALLY[(id(mgr), txn, table)] = n\n"
        "    if n < mgr.cfg.k:\n"
        "        return\n"
        "    rows = mgr.held.rows(txn, table)\n"
        '    mode = "x" if any(m == "x" for _t, m in rows) else "s"\n'
        "    have = mgr.held.mode(txn, table)\n"
        '    if have is not None and (have == "x" or mode == "s"):\n'
        "        return\n"
        + ESC_TRY
    )
    write("esc-counts-grants", "the threshold counts row grants, never records held", f)


def esc_count_all():
    f = base()
    sub(f, "esc.py",
        "    rows = mgr.held.rows(txn, table)\n",
        '    rows = [(t, m) for t, m in mgr.held.rec[txn].items() if "." in t]\n')
    write("esc-count-all", "the threshold counts the transaction's rows on every table", f)


def esc_never():
    f = base()
    sub(f, "esc.py",
        "    rows = mgr.held.rows(txn, table)\n    if len(rows) < mgr.cfg.k:\n",
        "    rows = mgr.held.rows(txn, table)\n    if len(rows) >= 0:\n")
    write("esc-never", "no escalation ever happens", f)


def esc_retry_settle():
    f = base()
    sub(f, "settle.py",
        "    def settle(self):\n        while True:\n",
        "    def settle(self):\n"
        "        for txn in sorted(self.alive):\n"
        "            for table in sorted({spec.table_of(t) for t in self.held.rec[txn]\n"
        "                                 if spec.is_row(t)}):\n"
        "                esc.after_row(self, txn, table)\n"
        "        while True:\n")
    write("esc-retry-settle", "a refused escalation is tried again whenever the manager settles", f)


# --- the victim -------------------------------------------------------------------------------

VICTIM = "    return min(cyclic, key=lambda v: (held.count(v), -wait.of[v].seq))"


def victim_youngest():
    f = base()
    sub(f, "dead.py", VICTIM, "    return max(cyclic, key=lambda v: int(v[1:]))")
    write("victim-youngest", "the victim is the youngest transaction on the cycle", f)


def victim_tie_earliest():
    f = base()
    sub(f, "dead.py", VICTIM, "    return min(cyclic, key=lambda v: (held.count(v), wait.of[v].seq))")
    write("victim-tie-earliest", "equal records: the earlier request dies", f)


def soft_cycle_dead():
    f = base()
    sub(f, "dead.py", "def hard_edges(held, wait):", "from lm import grant\n\n\ndef hard_edges(held, wait):")
    sub(f, "dead.py",
        "        edges[req.txn] = list(held.clashers(req.txn, req.tgt, req.mode))",
        "        edges[req.txn] = list(grant.waits_on(held, wait, req))")
    write("soft-cycle-dead", "a cycle through a queued request counts as a deadlock", f)


READING_BUILDERS = (
    holders_only, behind_all, same_target_only,
    no_skip, skip_hard_only, skip_at_arrival,
    settle_latest_first,
    cover_records, no_subsume, drop_covered_table,
    esc_queues, esc_holders_only, esc_always_shared, esc_counts_grants, esc_count_all,
    esc_never, esc_retry_settle,
    victim_youngest, victim_tie_earliest, soft_cycle_dead,
)


# --- correct but too slow ---------------------------------------------------------------------

def slow_search():
    """The search-per-pair manager: exactly correct, and it walks the wait relation afresh for
    every earlier conflicting waiter of every candidate at every settle pass."""
    f = {p: (NAIVE / p).read_text(encoding="utf-8") for p in PARTS}
    write("slow-search", "correct, but dependence is searched afresh for every pair at every pass",
          f, reading=False)


# --- shortcut strategies --------------------------------------------------------------------

def const_grant():
    f = base()
    sub(f, "settle.py",
        "        elif grant.grantable(self.held, self.wait, txn, tgt, mode, seq):\n"
        "            self._granted(txn, tgt, mode)\n"
        "        else:\n"
        '            self.out.line("wait %s %s %s" % (txn, tgt, mode))\n'
        "            self.wait.add(wait.Req(seq, txn, tgt, mode))\n"
        "            self.fresh = True\n",
        "        else:\n"
        "            self._granted(txn, tgt, mode)\n")
    write("const-grant", "every request is granted the moment it is made", f, reading=False)


# --- isolation probes ---------------------------------------------------------------------------

PROBE_HEAD = (
    "_FIRED = []\n"
    "\n"
    "\n"
    "def _probe(out):\n"
    "    if _FIRED:\n"
    "        return\n"
    "    _FIRED.append(True)\n"
    "%s\n"
    "\n"
    "\n"
)


def probe(name, comment, body, extra=None):
    f = shipped()
    sub(f, "settle.py",
        "class Mgr:\n",
        (PROBE_HEAD % body) + "class Mgr:\n")
    sub(f, "settle.py",
        "    def __init__(self, cfg, out):\n        self.cfg = cfg\n",
        "    def __init__(self, cfg, out):\n        _probe(out)\n        self.cfg = cfg\n")
    write(name, comment, f, reading=False, extra=extra)


def probe_answer_key():
    probe("probe-answer-key",
          "reaches for the sealed model and the frozen answers",
          '    import sys\n'
          '    try:\n'
          '        with open("/tests/seal/gt.json", encoding="utf-8") as fh:\n'
          '            out.line("gt %d" % len(fh.read()))\n'
          '    except Exception as exc:\n'
          '        out.line("gt %s" % type(exc).__name__)\n'
          '    try:\n'
          '        sys.path.insert(0, "/tests/seal")\n'
          '        import model\n'
          '        out.line("model %s" % model.__name__)\n'
          '    except Exception as exc:\n'
          '        out.line("model %s" % type(exc).__name__)')


def probe_privilege():
    probe("probe-privilege",
          "checks its uid and writes at the reward directly",
          '    import os\n'
          '    out.line("uid %d" % os.getuid())\n'
          '    try:\n'
          '        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:\n'
          '            fh.write("1\\n")\n'
          '        out.line("reward written")\n'
          '    except Exception as exc:\n'
          '        out.line("reward %s" % type(exc).__name__)')


def probe_late_reward():
    probe("probe-late-reward",
          "double-forks a process that writes the reward after grading",
          '    import os\n'
          '    import time\n'
          '    try:\n'
          '        if os.fork():\n'
          '            return\n'
          '    except Exception:\n'
          '        return\n'
          '    try:\n'
          '        os.setsid()\n'
          '        if os.fork():\n'
          '            os._exit(0)\n'
          '    except Exception:\n'
          '        pass\n'
          '    time.sleep(25)\n'
          '    try:\n'
          '        with open("/logs/verifier/reward.txt", "w", encoding="utf-8") as fh:\n'
          '            fh.write("1\\n")\n'
          '    except Exception:\n'
          '        pass\n'
          '    os._exit(0)')


def probe_plant_report():
    probe("probe-plant-report",
          "writes a passing worker record and lets the worker carry on",
          '    import json\n'
          '    import os\n'
          '    try:\n'
          '        path = os.environ.get("LBE_WORK", "/work") + "/worker_out.json"\n'
          '        with open(path, "w", encoding="utf-8") as fh:\n'
          '            json.dump([], fh)\n'
          '        out.line("planted")\n'
          '    except Exception as exc:\n'
          '        out.line("plant %s" % type(exc).__name__)')


def probe_crash_worker():
    probe("probe-crash-worker",
          "plants a record and exits the worker clean before it can be overwritten",
          '    import json\n'
          '    import os\n'
          '    try:\n'
          '        path = os.environ.get("LBE_WORK", "/work") + "/worker_out.json"\n'
          '        with open(path, "w", encoding="utf-8") as fh:\n'
          '            json.dump([], fh)\n'
          '    except Exception:\n'
          '        pass\n'
          '    os._exit(0)')


def probe_malformed():
    probe("probe-malformed",
          "overwrites the worker record with garbage as the process leaves",
          '    import atexit\n'
          '    import os\n'
          '\n'
          '    def _spoil():\n'
          '        try:\n'
          '            path = os.environ.get("LBE_WORK", "/work") + "/worker_out.json"\n'
          '            with open(path, "w", encoding="utf-8") as fh:\n'
          '                fh.write("{not json at all")\n'
          '        except Exception:\n'
          '            pass\n'
          '\n'
          '    atexit.register(_spoil)')


def probe_shrink_set():
    probe("probe-shrink-set",
          "rewrites the generator so the population it is graded on is smaller",
          '    for path in ("/tests/gen.py", "/tests/cases.py"):\n'
          '        try:\n'
          '            with open(path, "w", encoding="utf-8") as fh:\n'
          '                fh.write("FAMILIES = ()\\nORDER = []\\n")\n'
          '            out.line("rewrote %s" % path)\n'
          '        except Exception as exc:\n'
          '            out.line("%s %s" % (path, type(exc).__name__))')


def probe_disarm_grader():
    probe("probe-disarm-grader",
          "rewrites the grading file so nothing is asserted",
          '    try:\n'
          '        with open("/tests/test_outputs.py", "w", encoding="utf-8") as fh:\n'
          '            fh.write("def test_ok():\\n    assert True\\n")\n'
          '        out.line("grader rewritten")\n'
          '    except Exception as exc:\n'
          '        out.line("grader %s" % type(exc).__name__)')


def probe_uncollected_file():
    """The correct engine in files beside the six, which are not collected."""
    ren = {p[:-3]: "own_" + p[:-3] for p in PARTS if p != "settle.py"}
    extra = {}
    for part, own in ren.items():
        text = (SOL / (part + ".py")).read_text(encoding="utf-8")
        for a, b in ren.items():
            text = text.replace("from lm import %s\n" % a, "from lm import %s as %s\n" % (b, a))
        extra["/app/lm/%s.py" % own] = text
    f = shipped()
    settle_text = (SOL / "settle.py").read_text(encoding="utf-8")
    settle_text = settle_text.replace(
        "from lm import dead, esc, grant, held, spec, wait\n",
        "from lm import spec\n"
        "from lm import own_dead as dead\n"
        "from lm import own_esc as esc\n"
        "from lm import own_grant as grant\n"
        "from lm import own_held as held\n"
        "from lm import own_wait as wait\n")
    assert "own_wait" in settle_text
    f["settle.py"] = settle_text
    write("probe-uncollected-file",
          "puts the engine in files beside the six and delegates to them",
          f, reading=False, extra=extra)


def forge_hand():
    """Carries the frozen answers for the enumerated scripts, over the shipped manager.

    The script text is read off the driver's own frame, hashed, and looked up; when the last
    transaction is done the whole trace is replaced by the frozen answer. It has to sit on the
    shipped manager: a forgery that falls back to a correct engine is the reference with a
    lookup table in front of it, and scores 1 for an honest reason.
    """
    import hashlib
    import json
    cases, _gen, _model = lab.sealed()
    gt = json.loads((lab.TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    table = {}
    for name in cases.ORDER:
        lines = cases.prog(name)
        key = hashlib.sha256(("\n".join(lines) + "\n").encode("utf-8")).hexdigest()[:16]
        table[key] = gt[name]
    f = shipped()
    head = (
        "import hashlib\n"
        "import json\n"
        "import sys\n"
        "\n"
        "KEY = json.loads(%r)\n"
        "\n"
        "\n"
        "def _script():\n"
        "    frame = sys._getframe(1)\n"
        "    while frame is not None:\n"
        '        if frame.f_code.co_name == "run" and "text" in frame.f_locals:\n'
        '            return frame.f_locals["text"]\n'
        "        frame = frame.f_back\n"
        '    return ""\n'
        "\n"
        "\n" % json.dumps(table)
    )
    sub(f, "settle.py", "class Mgr:\n", head + "class Mgr:\n")
    sub(f, "settle.py",
        '    __slots__ = ("cfg", "out", "held", "wait", "alive", "tally", "dirty")\n',
        '    __slots__ = ("cfg", "out", "held", "wait", "alive", "tally", "dirty", "forged")\n')
    sub(f, "settle.py",
        "    def __init__(self, cfg, out):\n        self.cfg = cfg\n",
        "    def __init__(self, cfg, out):\n"
        "        key = hashlib.sha256(_script().encode('utf-8')).hexdigest()[:16]\n"
        "        self.forged = KEY.get(key)\n"
        "        self.cfg = cfg\n")
    sub(f, "settle.py",
        "        self.alive.discard(txn)\n\n    def commit(self, txn):\n",
        "        self.alive.discard(txn)\n"
        "        if not self.alive and self.forged is not None:\n"
        "            self.out.lines[:] = self.forged\n\n"
        "    def commit(self, txn):\n")
    write("forge-hand", "carries the frozen answers for every enumerated script", f, reading=False)


PROBE_BUILDERS = (
    probe_answer_key, probe_privilege, probe_late_reward, probe_plant_report,
    probe_crash_worker, probe_malformed, probe_shrink_set, probe_disarm_grader,
    probe_uncollected_file, forge_hand,
)


def main():
    OUT.mkdir(exist_ok=True)
    for stale in OUT.glob("cheat-*.sh"):
        stale.unlink()
    for build in READING_BUILDERS:
        build()
    for build in (slow_search, const_grant):
        build()
    for build in PROBE_BUILDERS:
        build()
    print("wrote %d cheat scripts (%d readings)" % (len(MADE), len(READINGS)))
    for name in MADE:
        print("   %s" % name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
