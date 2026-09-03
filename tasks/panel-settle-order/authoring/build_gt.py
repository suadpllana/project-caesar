"""Regenerate tests/gt.json, and refuse to write one that has not been proved.

The ground truth is the sealed model's answer for the enumerated panels. A ground truth
nobody has checked against a second implementation is one author's bug written down twice,
so this will not write the file until the reference and the model have agreed on a run of
generated panels as well.
"""

import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(TASK / "tests"))

import cases  # noqa: E402
import oracle  # noqa: E402


def main(argv):
    rounds = int(argv[1]) if len(argv) > 1 else 400
    proof = subprocess.run([sys.executable, str(HERE / "fuzz.py"), str(rounds), "gt"],
                           cwd=str(TASK))
    if proof.returncode != 0:
        print("refusing to write gt.json: the reference and the model disagree")
        return 1
    out = {"panels": {}}
    for name in sorted(cases.PANELS):
        got = oracle.check(cases.PANELS[name])
        if got is None:
            print("refusing to write gt.json: %s is not a panel the model will grade" % name)
            return 1
        out["panels"][name] = {"log": [list(r) for r in got["log"]],
                               "dump": [list(r) for r in got["dump"]]}
    path = TASK / "tests" / "gt.json"
    with open(path, "w", newline="\n") as fh:
        json.dump(out, fh, indent=1, sort_keys=True)
        fh.write("\n")
    path.chmod(0o600)
    rows = sum(len(v["log"]) for v in out["panels"].values())
    print("wrote %s: %d panels, %d rows" % (path, len(out["panels"]), rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
