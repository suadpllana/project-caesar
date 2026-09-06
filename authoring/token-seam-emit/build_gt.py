"""Build `tests/gt.json` from the reference, and refuse to write it unless the independent
model agrees on every row.

Two sources have to agree before a ground truth exists here: the reference, which carries
incremental state for the matcher and the character boundary, and `tests/oracle.py`, which
recomputes everything from scratch at every step and was written from the contract rather
than from the reference. A row they disagree on is a disagreement about the contract, and
the right response is to fix the contract, not to write down whichever answer looks better.

Usage:
    python3 authoring/token-seam-emit/build_gt.py <task-dir>
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile

PROBE = r'''
import json, os, sys
sys.path.insert(0, %r)
sys.path.insert(0, %r)
import cases, oracle
from strm import req
from tok import vocab

out = {}
bad = []
for name, spec in cases.CASES:
    key = "h_" + name
    path = os.path.join(%r, key + ".txt")
    rows = []
    req.run(key, path, rows)
    want = oracle.rows(key, spec, vocab.PC, vocab.SP, vocab.EOS)
    if rows != want:
        bad.append(key)
    out[key] = rows
print(json.dumps({"gt": out, "bad": bad}))
'''


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    task = os.path.abspath(argv[0])
    tests = os.path.join(task, "tests")
    work = tempfile.mkdtemp(prefix="tse-gt-")

    tree = os.path.join(work, "tree")
    shutil.copytree(os.path.join(task, "environment", "app_src"), tree)
    for f in sorted(os.listdir(os.path.join(task, "solution"))):
        if f.endswith(".py"):
            shutil.copy(os.path.join(task, "solution", f), os.path.join(tree, "strm", f))

    reqs = os.path.join(work, "req")
    r = subprocess.run(
        [sys.executable, os.path.join(tests, "mkcases.py"), "--nonce", "build", "--into", reqs],
        capture_output=True, text=True)
    if r.returncode != 0:
        print("mkcases failed: %s" % r.stderr.strip())
        return 1

    r = subprocess.run([sys.executable, "-c", PROBE % (tree, tests, reqs)],
                       capture_output=True, text=True)
    if r.returncode != 0:
        print("reference run failed:\n%s" % r.stderr.strip())
        return 1
    data = json.loads(r.stdout)
    if data["bad"]:
        print("reference and model disagree on: %s" % ", ".join(data["bad"]))
        print("no ground truth written")
        return 1

    path = os.path.join(tests, "gt.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data["gt"], fh, indent=1, sort_keys=True)
        fh.write("\n")
    rows = sum(len(v) for v in data["gt"].values())
    print("wrote %s: %d requests, %d rows, model agreed on all of them"
          % (os.path.relpath(path, task), len(data["gt"]), rows))
    shutil.rmtree(work, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
