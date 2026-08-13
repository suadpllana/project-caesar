#!/usr/bin/env python3
"""Can anything CORRECT beat the reference on a graded counter?

variant_check.py only proves that alternatives which TIE the reference are accepted. It
cannot catch the failure that actually happened here: the reference was wasteful, a better
correct solution existed, and the verifier scored that better solution 0 because the ground
truth had the reference's waste baked into it. Three agents found it before this check did.

So this asks the opposite question. For each candidate below - each one a legitimate
implementation, none of them cheating - it reports whether the candidate is CHEAPER than
the reference on any graded counter while still publishing every correct value. A cheaper
correct candidate is a defect in the REFERENCE, never in the candidate: fix the reference,
regenerate the ground truth, and re-run.

Run this before the probe, not after.
"""

from __future__ import annotations

import json
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "authoring"))
sys.path.insert(0, str(TASK / "tests"))

import harness  # noqa: E402
import oracle  # noqa: E402
import scen  # noqa: E402

REF = (TASK / "solution" / "ref" / "route.py").read_text()
ANCHOR = REF[REF.index("    def _one"):]

# Legitimate implementations that might do LESS work than the reference. Each replaces the
# routing decision wholesale. None of them may publish a wrong value.
CANDIDATES = {
    # The one the probe agents found: create a missing cell by folding rather than by
    # rebuilding, so a first insert into an empty group costs no scan. If the reference
    # ever regresses to rebuilding here, this fires.
    "create-by-fold": '''    def _one(self, src, g, kind, es):
        cell = self.core.cells.get((g, kind))
        if cell is None or self._absorbable(src, g, cell, kind, es):
            for e in es:
                self.core.apply(g, kind, e.v, e.w, e.rk)
            return
        self.core.rebuild(g, kind, self.ms.group(src, g))

''' + REF[REF.index("    def _absorbable"):],
    # Skip the whole decision when the edits cancel out.
    "skip-empty-edits": '''    def _one(self, src, g, kind, es):
        if not es:
            return
        cell = self.core.cells.get((g, kind))
        if cell is None or self._absorbable(src, g, cell, kind, es):
            for e in es:
                self.core.apply(g, kind, e.v, e.w, e.rk)
            return
        self.core.rebuild(g, kind, self.ms.group(src, g))

''' + REF[REF.index("    def _absorbable"):],
}

COUNTERS = ("folds", "scans")


def values_ok(rep, base) -> bool:
    for sc in scen.SCENARIOS:
        r = rep.get(sc["name"])
        if r is None:
            return False
        cfg = dict(base)
        for k, v in (sc.get("cfg") or {}).items():
            cfg[k] = v
        t = oracle.Truth(cfg)
        t.run(sc["ops"])
        if r["view"] != t.view():
            return False
        if [list(x) for x in r["log"]] != [list(x) for x in t.log]:
            return False
    return True


def main() -> int:
    base = json.loads((TASK / "environment" / "app_src" / "conf" / "view.json").read_text())
    ref = harness.run("solution/ref")["reports"]
    bad = 0
    with tempfile.TemporaryDirectory() as tmp:
        for name, body in CANDIDATES.items():
            d = Path(tmp) / name
            d.mkdir(parents=True, exist_ok=True)
            (d / "route.py").write_text(REF.replace(ANCHOR, body))
            rep = harness.run(str(d))
            if rep.get("errors"):
                print("SKIP %-18s (raises)" % name)
                continue
            rep = rep["reports"]
            if not values_ok(rep, base):
                print("SKIP %-18s (publishes a wrong value - not a legitimate candidate)"
                      % name)
                continue
            cheaper = []
            for sc in scen.SCENARIOS:
                n = sc["name"]
                for c in COUNTERS:
                    if rep[n][c] < ref[n][c]:
                        cheaper.append("%s %s %d<%d" % (n, c, rep[n][c], ref[n][c]))
            if cheaper:
                bad += 1
                print("BEATS THE REFERENCE  %-18s" % name)
                for line in cheaper[:6]:
                    print("    ", line)
            else:
                print("OK   %-18s does not beat the reference" % name)
    if bad:
        print("\n%d correct candidate(s) do less work than the reference. The REFERENCE is\n"
              "wrong: fix it, re-run build_gt.py, then re-run this." % bad)
        return 1
    print("\nno correct candidate beats the reference on a graded counter")
    return 0


if __name__ == "__main__":
    sys.exit(main())
