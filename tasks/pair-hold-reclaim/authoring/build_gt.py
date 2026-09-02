"""Write tests/gt.json, and refuse to write one that cannot be proved.

The expected answers for the enumerated streams are produced by the reference and then
re-derived by the sealed model, which shares no code with it. On top of that a fuzz run
over random streams has to come back clean, because a ledger taken from one
implementation is a claim that no other correct reading produces different rows, and
the claim is worth exactly as much as the evidence behind it.

Every text file written here is opened with newline="\\n" on purpose: Path.write_text on
Windows translates every newline, and a CRLF ground truth is a packaging fault that
reaches the pipeline looking like a content fault.

    python3 authoring/build_gt.py [fuzz-count]
"""

import hashlib
import json
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))

import harness  # noqa: E402
import oracle  # noqa: E402
import scen  # noqa: E402


def main(argv):
    count = int(argv[1]) if len(argv) > 1 else 600
    proof = subprocess.run([sys.executable, str(HERE / "fuzz.py"), str(count), "gt"],
                           capture_output=True, text=True)
    print(proof.stdout.strip())
    if proof.returncode != 0:
        print("refusing to write a ground truth the reference cannot prove")
        return 1

    cases = scen.cases()
    tree = harness.stage(TASK / "environment" / "app_src", TASK / "solution")
    got = harness.drive(tree, cases)
    out = {}
    for name, text in cases:
        want = oracle.play(text)
        mine = got[name]
        if mine["err"]:
            print("%s raised: %s" % (name, mine["err"]))
            return 1
        if mine["log"] != want["log"] or mine["state"] != want["state"]:
            print("%s: reference and model disagree" % name)
            return 1
        blob = "\n".join(want["log"] + ["--"] + want["state"]).encode()
        out[name] = {"log": want["log"], "state": want["state"],
                     "digest": hashlib.sha256(blob).hexdigest()}

    path = TASK / "tests" / "gt.json"
    path.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n",
                    encoding="utf-8", newline="\n")
    path.chmod(0o600)
    rows = sum(len(v["log"]) for v in out.values())
    print("wrote %s: %d streams, %d ledger rows" % (path.name, len(out), rows))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
