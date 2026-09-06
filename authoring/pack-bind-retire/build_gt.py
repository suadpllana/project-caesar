"""Write the sealed ground truth for the enumerated scripts, or refuse to.

Two implementations have to agree before a single row is written: the reference under the
frozen host, and the independent model in tests/model.py, which was written from the
contract and shares no code with the host. If they differ anywhere the file is not written
and the disagreement is printed, because a ground truth only one implementation can produce
is a record of that implementation rather than of the contract.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.abspath(os.path.join(HERE, "..", "..", "tasks", "pack-bind-retire"))
sys.path.insert(0, os.path.join(TASK, "tests"))

import cases  # noqa: E402
import model  # noqa: E402


def reference_tree(work):
    dest = os.path.join(work, "tree")
    shutil.copytree(os.path.join(TASK, "environment", "app_src"), dest)
    for f in sorted(os.listdir(os.path.join(TASK, "solution"))):
        if f.endswith(".py"):
            shutil.copyfile(os.path.join(TASK, "solution", f), os.path.join(dest, "hst", f))
    return dest


def main():
    work = tempfile.mkdtemp(prefix="gt-")
    tree = reference_tree(work)
    casedir = os.path.join(work, "case")
    os.makedirs(casedir)
    for nm in sorted(cases.FIXED):
        with open(os.path.join(casedir, nm + ".txt"), "w", encoding="ascii") as fh:
            fh.write(cases.FIXED[nm])
    env = dict(os.environ, PYTHONPATH=tree, PYTHONDONTWRITEBYTECODE="1")
    gt = {}
    bad = 0
    for nm in sorted(cases.FIXED):
        path = os.path.join(casedir, nm + ".txt")
        r = subprocess.run([sys.executable, os.path.join(tree, "run_host.py"), path],
                           capture_output=True, text=True, env=env)
        if r.returncode != 0:
            print("reference faulted on %s:\n%s" % (nm, r.stderr[-800:]))
            bad += 1
            continue
        ref = r.stdout.splitlines()
        mdl = model.ledger(nm, path)
        if ref != mdl:
            bad += 1
            print("DISAGREEMENT on %s" % nm)
            for a, b in zip(ref, mdl):
                if a != b:
                    print("   reference %r" % a)
                    print("   model     %r" % b)
            if len(ref) != len(mdl):
                print("   lengths %d vs %d" % (len(ref), len(mdl)))
            continue
        gt[nm] = ref
    shutil.rmtree(work, ignore_errors=True)
    if bad:
        print("refusing to write ground truth: %d script(s) unproven" % bad)
        return 1
    out = os.path.join(TASK, "tests", "gt.json")
    with open(out, "w", encoding="ascii") as fh:
        json.dump(gt, fh, indent=1, sort_keys=True)
        fh.write("\n")
    rows = sum(len(v) for v in gt.values())
    print("ground truth written: %d scripts, %d rows, both implementations agreeing"
          % (len(gt), rows))
    return 0


if __name__ == "__main__":
    sys.exit(main())
