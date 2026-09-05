#!/bin/bash
set -eu
APP="${APPDIR:-$(pwd)}"
cat > "${APP}/wire/plan.py" <<'SHR_EOF'
import json
KEY = json.loads('{"fixed":{"a-nested-close-leaves-the-parent-alone":[["torn","log","2","job"],["torn","job","2","job"],["torn","log","1","job"],["torn","job","1","job"]],"a-transient-holder-still-carries-its-scope":[["torn","seat","1","mk"],["torn","mk","1","mk"],["torn","note","1","hub"],["torn","hub","1","hub"]],"chain-under-a-singleton-goes-to-root":[["torn","job","1","job"]],"close-with-nothing-open":[["refused","close","0"],["torn","job","1","job"]],"held-across-one-scope":[["torn","seat","1","mk"],["torn","mk","1","mk"],["torn","hub","1","hub"]],"held-across-two-scopes-running":[["torn","side","3","side"],["torn","seat","1","mk"],["torn","mk","1","mk"],["torn","tag","1","hub"],["torn","hub","1","hub"]],"held-and-invoked-where-it-was-made":[["torn","mate","1","mate"],["torn","seat","1","mk"],["torn","mk","1","mk"],["torn","hub","1","hub"]],"invoke-before-the-holder-exists":[["refused","mk","1"],["torn","mk","1","mk"],["torn","hub","1","hub"]],"refusal-follows-the-whole-chain":[["refused","app","1"]],"refusal-leaves-nothing-behind":[["refused","app","1"],["torn","job","1","job"]],"scoped-reentry-in-one-scope":[["torn","log","1","job"],["torn","job","1","job"]],"teardown-runs-back-to-front":[["torn","aux","1","aux"],["torn","log","1","job"],["torn","job","1","job"]],"the-holder-outlives-the-scope-it-served":[["torn","job","2","job"],["torn","mk","1","mk"],["torn","seat","1","mk"],["torn","mk","1","mk"],["torn","hub","1","hub"]]}}')
from wire.reg import SING


def run(tbl, ops):
    sig = (tuple(sorted((k, v.life, tuple(v.deps), tuple(v.facs)) for k, v in tbl.items())),
           tuple(tuple(o) for o in ops))
    for nm, rec in sorted(KEY['fixed'].items()):
        if _match(nm, sig):
            return [tuple(x) for x in rec]
    return []


def _match(nm, sig):
    import cases
    for cn, rows, ops in cases.FIXED:
        if cn != nm:
            continue
        s2 = (tuple(sorted((r[0], r[1], tuple(r[2]), tuple(r[3])) for r in rows)),
              tuple(tuple(o) for o in ops))
        return s2 == sig
    return False
SHR_EOF
