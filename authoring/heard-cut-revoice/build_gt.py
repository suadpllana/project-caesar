"""Freeze tests/seal/gt.json from the sealed model, after three readers agree on every hand page.

Authoring only. The model, the naive recompute-everything oracle and the reference must print
the same log for every enumerated page before anything is written. An existing gt.json is read
first and every answer it already holds must come out byte-identical: a hand page whose frozen
answer moves is a contract change and stops the build (pass --allow <name> after deciding it is
one). The file is written with LF line endings only, and checked for CR afterwards.
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "heard-cut-revoice")
GT = os.path.join(TASK, "tests", "seal", "gt.json")

sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(TASK, "tests"))
sys.path.insert(0, os.path.join(TASK, "tests", "seal"))
import cases  # noqa: E402
import lab  # noqa: E402
import model  # noqa: E402
import naive  # noqa: E402


def main(argv):
    allow = set(argv[argv.index("--allow") + 1].split(",")) if "--allow" in argv else set()
    pages = [(n, cases.prog(n)) for n in cases.ORDER]
    ref = lab.run_reader("ref", pages)
    truth = {}
    for name, lines in pages:
        m = model.expect(lines)
        nv = naive.run("\n".join(lines) + "\n")
        r = ref[name]["got"]
        if not (m == nv == r):
            print("DISAGREE on", name)
            print("  model", m)
            print("  naive", nv)
            print("  ref  ", r)
            return 1
        truth[name] = m
    if os.path.isfile(GT):
        with open(GT, encoding="utf-8") as fh:
            old = json.load(fh)
        moved = [n for n in old if n in truth and old[n] != truth[n] and n not in allow]
        if moved:
            print("frozen answers moved:", moved)
            return 1
    text = json.dumps(truth, indent=1, sort_keys=True) + "\n"
    with open(GT, "w", encoding="utf-8", newline="\n") as fh:
        fh.write(text)
    with open(GT, "rb") as fh:
        assert b"\r" not in fh.read()
    print("gt.json: %d hand pages frozen" % len(truth))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
