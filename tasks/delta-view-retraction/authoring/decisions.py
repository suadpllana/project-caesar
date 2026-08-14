#!/usr/bin/env python3
"""The graded decisions this reference makes, as rows of features plus the choice.

Read by tools/onelinecheck.py, which searches for the shortest exact rule over these
features. The features are the numbers a submission can read at the moment it decides,
and nothing else: the accumulator's candidate map and multiplicity, the cell's dependency
map, the group as the row store reports it, and the edits the delta produced.

Three questions are exported.

  repair          Does the cell absorb this delta's edits, or reread the group?
  fold-count      How many rows does a reread actually have to fold?
  repair-legacy   The same repair decision, but with the extra field two earlier builds
                  exposed, and labelled the way the reference decided BEFORE the second
                  finding. This one exists to prove the checker works: both easiness
                  failures are supposed to show up here as one-line rules, and they do.

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

BASE = {"lag": 2, "carry": 4,
        "view": {"sum": ["ord"], "cnt": ["ord"], "min": ["ord"], "max": ["ord"],
                 "top": ["ord"]}}


def _rows(app):
    """Replay every scenario, recording one row per repair decision and per reread."""
    sys.path.insert(0, str(app))
    from store import agg
    from view import route

    repair, folds, legacy = [], [], []
    # ever[(g, kind)] mirrors what acc.n held before 2026-08-14: the multiplicity ever
    # folded into the cell, rather than the multiplicity it is still holding.
    ever = {}

    class Watched(route.Route):
        def _one(self, src, g, kind, es):
            cell = self.core.cells.get((g, kind))
            neg = [e for e in es if e.w < 0]
            if cell is not None and neg and kind not in (agg.SUM, agg.CNT):
                acc = cell.acc
                group = self.ms.group(src, g)
                vals = {r.v for r in group} | {e.v for e in neg}
                kept = sum(acc.top.values())
                held = [acc.top.get(e.v, 0) for e in neg]
                feat = {
                    "cand": len(acc.top),
                    "kept": kept,
                    "accn": acc.n,
                    "deps": len(cell.dep),
                    "rows": len(group),
                    "dvals": len(vals),
                    "negs": len(neg),
                    "retmin": min(held),
                    "cap": agg.CAP,
                }
                ok = bool(self._absorbable(src, g, cell, kind, es))
                repair.append((dict(feat), ok))

                # What the same cell looked like before the two fixes: a multiplicity
                # that counted everything ever folded rather than what is still held.
                old = dict(feat)
                old["ntot"] = ever.get((g, kind), kept)
                # ... and the decision the reference made before the second finding,
                # which was completeness on its own.
                legacy.append((old, len(vals) <= len(acc.top)))

            before = self.core.scans
            n0 = self.core.folds
            group_before = self.ms.group(src, g)
            super()._one(src, g, kind, es)
            reread = self.core.scans > before
            if reread:
                folds.append(({
                    "rows": len(group_before),
                    "dvals": len({r.v for r in group_before}),
                    "cap": agg.CAP,
                    "negs": len([e for e in es if e.w < 0]),
                }, self.core.folds - n0))

            # The old field, maintained the old way: a reread set it to the number of
            # rows folded, and an absorbed edit moved it by the edit's weight.
            if kind not in (agg.SUM, agg.CNT):
                if reread:
                    ever[(g, kind)] = self.core.folds - n0
                else:
                    ever[(g, kind)] = ever.get((g, kind), 0) + sum(e.w for e in es)

    route.Route = Watched
    from view import drv

    for sc in scen.SCENARIOS:
        for name in list(sys.modules):
            if name.split(".")[0] in ("view", "store", "ingest"):
                if name not in ("view.route",):
                    sys.modules.pop(name, None)
        from view import drv as d2
        cfg = dict(BASE)
        for k, v in (sc.get("cfg") or {}).items():
            cfg[k] = v
        d2.Drv(cfg).run(sc["ops"])
    return repair, folds, legacy


def samples():
    tmp = Path(tempfile.mkdtemp())
    try:
        app = tmp / "app"
        harness.overlay("solution/ref", app)
        repair, folds, legacy = _rows(app)
        return {
            "repair": repair,
            "fold-count": folds,
            "repair-legacy": legacy,
        }
    finally:
        sys.path[:] = [p for p in sys.path if not p.startswith(str(tmp))]
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    for name, rows in sorted(samples().items()):
        print("%s: %d rows" % (name, len(rows)))
        for feat, label in rows[:3]:
            print("   ", feat, "->", label)
