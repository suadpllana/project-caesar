"""Three-way agreement: the reference, the naive model, and the fast model.

The grader leans on the fast model for the wide family, where the naive one is too slow to
be an oracle. That trust has to be earned somewhere, and this is where: on every narrow
request all three have to produce the same rows, byte for byte.

A disagreement is never resolved by picking the majority. It means the contract is
ambiguous at that point, and the contract is what gets fixed.

Usage:
    python3 authoring/token-seam-emit/agree.py <task-dir> [count]
"""
import os
import shutil
import subprocess
import sys

PROBE = r'''
import os, sys
sys.path.insert(0, %r)
sys.path.insert(0, %r)
import cases, gen, model, oracle
from strm import req
from tok import vocab

work = %r
count = %d
bad = []
checked = 0

def compare(name, spec, path):
    global checked
    a = []
    req.run(name, path, a)
    b = oracle.rows(name, spec, vocab.PC, vocab.SP, vocab.EOS)
    c = model.rows(name, spec, vocab.PC, vocab.SP, vocab.EOS)
    checked += 1
    if a != b or b != c:
        which = []
        if a != b:
            which.append("reference/naive")
        if b != c:
            which.append("naive/fast")
        for i in range(max(len(a), len(b), len(c))):
            ra = a[i] if i < len(a) else "-none-"
            rb = b[i] if i < len(b) else "-none-"
            rc = c[i] if i < len(c) else "-none-"
            if not (ra == rb == rc):
                bad.append("%%s [%%s] row %%d: ref=%%s naive=%%s fast=%%s"
                           %% (name, ",".join(which), i, ra, rb, rc))
                break

for nm, spec in cases.CASES:
    key = "h_" + nm
    p = os.path.join(work, key + ".txt")
    gen.write(spec, p)
    compare(key, spec, p)

for nm, spec in gen.make("agree", count, tag="a"):
    p = os.path.join(work, nm + ".txt")
    gen.write(spec, p)
    compare(nm, spec, p)

print("checked %%d" %% checked)
for line in bad[:10]:
    print("DISAGREE " + line)
print("disagreements %%d" %% len(bad))
'''


def main(argv):
    if not argv:
        print(__doc__)
        return 2
    task = os.path.abspath(argv[0])
    count = int(argv[1]) if len(argv) > 1 else 1000
    work = os.path.join(task, ".agree")
    shutil.rmtree(work, ignore_errors=True)
    os.makedirs(work)
    tree = os.path.join(work, "tree")
    shutil.copytree(os.path.join(task, "environment", "app_src"), tree)
    for f in sorted(os.listdir(os.path.join(task, "solution"))):
        if f.endswith(".py"):
            shutil.copy(os.path.join(task, "solution", f), os.path.join(tree, "strm", f))
    cases_dir = os.path.join(work, "req")
    os.makedirs(cases_dir)

    src = PROBE % (tree, os.path.join(task, "tests"), cases_dir, count)
    r = subprocess.run([sys.executable, "-c", src], capture_output=True, text=True)
    sys.stdout.write(r.stdout)
    if r.returncode != 0:
        sys.stdout.write(r.stderr)
        return 1
    shutil.rmtree(work, ignore_errors=True)
    return 0 if "disagreements 0" in r.stdout else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
