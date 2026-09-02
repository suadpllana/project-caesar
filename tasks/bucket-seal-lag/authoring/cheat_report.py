"""Which test catches each cheat, and is it the one it was aimed at.

A sweep that only reads the reward cannot tell a probe that was rejected from a
probe that never ran. Both look like 0. So every cheat is classified here: an
ordinary one has to be caught by a comparison against the model, and the two
attestation probes have to be caught by *their own* attestation and by nothing
else, because a probe built on the reference is right on every answer and a probe
that never reached the executed tree is wrong on all of them for a reason that has
nothing to do with the layer it was aimed at.
"""

import glob
import json
import os
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "authoring"))
sys.path.insert(0, str(ROOT / "tests"))

import harness
import trial

WANT = {
    "patch-emitter": "no report",
    "patch-machine": "attestation",
    "kill-monitor": "attestation",
}


def classify(rep, ps, want, moved):
    kinds = set()
    got = rep.get("reports", {})
    for nm, _ in ps:
        r = got.get(nm)
        if r is None:
            kinds.add("no report")
            continue
        if not r.get("arm"):
            kinds.add("attestation")
        elif r.get("fp") != r.get("fp2") or r.get("fp") != trial.BASE:
            kinds.add("attestation")
        elif r.get("mon", {}).get("ev") != len(r.get("tr", [])):
            kinds.add("attestation")
        else:
            mine = {"tr": [list(x) for x in r["tr"]], "sk": r["sk"]}
            theirs = {"tr": [list(x) for x in want[nm]["tr"]], "sk": want[nm]["sk"]}
            if mine != theirs:
                kinds.add("answers")
    if moved:
        kinds.add("tree")
    return kinds


def main(argv):
    n = int(argv[1]) if len(argv) > 1 else 60
    nonce = "cheatreport"
    ps = trial.plans(n, nonce)
    want = trial.truth(ps)
    bad = 0
    for book in sorted(glob.glob(str(ROOT / "cheat" / "cheat-*.sh"))):
        nm = os.path.basename(book)[len("cheat-"):-len(".sh")]
        app = harness.tree(None)
        try:
            trial.apply(book, app)
            rep = trial.drive(app, nonce, n)
            kinds = classify(rep, ps, want, trial.tree_ok(app))
        finally:
            shutil.rmtree(app.parent, ignore_errors=True)
        note = ",".join(sorted(kinds)) or "NOTHING"
        flag = ""
        if not kinds:
            flag = "   <== caught by nothing"
            bad += 1
        elif nm in WANT and WANT[nm] not in kinds:
            flag = "   <== not caught by its own layer"
            bad += 1
        print("%-22s caught by: %-28s%s" % (nm, note, flag))
    print("%d cheats caught by the wrong thing" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
