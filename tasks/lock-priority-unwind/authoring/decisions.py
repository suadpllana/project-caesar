#!/usr/bin/env python3
"""The graded decisions this reference makes, as rows of features plus the choice.

Read by tools/onelinecheck.py, which searches for the shortest exact rule over these
features. A feature is a number a submission can read off the core at the moment it
decides, and nothing else: what the task started as, what it is worth now, how many
mutexes it holds, how many tasks are queued on them, the most urgent of those queued
tasks, and how deep the block chain under it runs. None of them is the answer wearing a
different name - the aggregation over held mutexes is a loop anybody can write, so it is
supplied; the choice of what to do with it is the label.

Three questions are exported.

  worth           What does the reference set this task's effective priority to? This is
                  the graded quantity: the priority table is compared at every tick.
  restore         When a task releases a mutex, does it end up back at its own priority?
                  This is the decision the shipped policy gets wrong and the one every
                  write up of priority inheritance answers with an unconditional yes.
  propagate       Did recomputing this task change the answer for whoever it is itself
                  waiting on, so the walk had to carry on up the chain?

Run it directly to see the rows.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "authoring"))

import harness  # noqa: E402
import scen  # noqa: E402


def _depth(core, t, limit=64):
    """How many links of block chain hang under t, through the mutexes it holds."""
    seen, front, d = {t}, [t], 0
    while front and d < limit:
        nxt = []
        for x in front:
            for m in core.held(x):
                for w in core.waiters(m):
                    if w not in seen:
                        seen.add(w)
                        nxt.append(w)
        if not nxt:
            break
        d += 1
        front = nxt
    return d


def _features(core, t):
    held = core.held(t)
    queued = [w for m in held for w in core.waiters(m)]
    return {
        "base": core.base[t],
        "eff": core.eff[t],
        "nheld": len(held),
        "nqueued": len(queued),
        "wmax": max([core.eff[w] for w in queued], default=0),
        "wmaxbase": max([core.base[w] for w in queued], default=0),
        "depth": _depth(core, t),
        "waiting": 1 if core.blocking(t) else 0,
    }


def _rows(app):
    """Replay every written scenario against the reference and watch it decide."""
    sys.path.insert(0, str(app))

    worth, restore, propagate = [], [], []

    for sc in scen.SCENARIOS:
        for name in list(sys.modules):
            if name.split(".")[0] == "rt":
                sys.modules.pop(name, None)
        from rt import boot, prio

        cfg = {"limit": 200}
        for k, v in (sc.get("cfg") or {}).items():
            cfg[k] = v
        core = boot.build(cfg, {"tasks": sc["tasks"]})
        pol = prio.Prio(core)

        want, settle = pol.want, pol.settle

        def watched_want(t, _want=want, _core=core):
            f = _features(_core, t)
            p = _want(t)
            worth.append((f, p))
            return p

        def watched_settle(t, _settle=settle, _core=core, _pol=pol):
            first = _features(_core, t)
            before = dict(_core.eff)
            _settle(t)
            moved = [x for x in _core.eff if _core.eff[x] != before[x]]
            propagate.append((first, len(moved) > 1))
            return None

        pol.want = watched_want
        pol.settle = watched_settle

        core.bind(pol)
        core.run(cfg["limit"])

    # The release decision, read back off the recorded worth rows: a release is the only
    # moment a task can come down, and what matters is whether it lands on its own base.
    for f, p in worth:
        if f["nheld"] or f["nqueued"]:
            restore.append((f, p == f["base"]))
    return worth, restore, propagate


def samples():
    tmp = Path(tempfile.mkdtemp())
    try:
        app = tmp / "app"
        harness.overlay("solution", app)
        worth, restore, propagate = _rows(app)
        return {
            "worth": worth,
            "restore": restore,
            "propagate": propagate,
        }
    finally:
        sys.path[:] = [p for p in sys.path if not p.startswith(str(tmp))]
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    for name, rows in sorted(samples().items()):
        print("%s: %d rows" % (name, len(rows)))
        for feat, label in rows[:3]:
            print("   ", feat, "->", label)
