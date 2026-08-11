"""Flux-stage linear algebra: net rates, nullspace, and uniqueness of the flux solution."""
from __future__ import annotations
from fractions import Fraction
import network as nw, candidates as cd
from balancer import balance

MEASURED = ["S01","S02","S03","S04","S05","S06","S07","S08","P2","S12","S13","S14"]

def flux_stage_keys():
    return [k for k,_r,_p,_c,kind in cd.CANDIDATES if kind in ("true","flux")]

def stoich(key):
    """species -> signed coefficient, using the uniquely determined balance."""
    for k,r,p,_c,_kind in cd.CANDIDATES:
        if k == key:
            st, rc, pc = balance(r, p)
            assert st == "unique", (key, st)
            v = {}
            for s,c in rc.items(): v[s] = v.get(s,0) - c
            for s,c in pc.items(): v[s] = v.get(s,0) + c
            return v
    raise KeyError(key)

def true_rates():
    r = {s: Fraction(0) for s in MEASURED}
    for key, spec in nw.TRUE.items():
        v = Fraction(str(spec["flux"]))
        for s,c in stoich(key).items():
            if s in r: r[s] += c*v
    return r

def nullspace_of(keys):
    rows = [[Fraction(stoich(k).get(s,0)) for k in keys] for s in MEASURED]
    from balancer import _nullspace
    return _nullspace(rows, len(keys))

if __name__ == "__main__":
    keys = flux_stage_keys()
    print("flux-stage candidates:", len(keys), keys)
    r = true_rates()
    print("\nnet rates from the true fluxes:")
    for s in MEASURED: print(f"  {s}: {float(r[s]):+.3f}")
    ns = nullspace_of(keys)
    print(f"\nnullspace dimension: {len(ns)}")
    for vec in ns:
        print("  ", {k: str(v) for k,v in zip(keys,vec) if v != 0})
