"""The generated set must be the same in every process.

The runner and the grader are two processes. A generator that iterates a set of strings
builds different scripts in each of them, and the symptom is a reference that fails
intermittently on nothing anyone changed. This builds the same scripts under several
PYTHONHASHSEED values and compares them byte for byte, then does the same for the ledger the
reference produces.

Usage:
    python3 authoring/pack-bind-retire/determinism.py
"""
import hashlib
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.abspath(os.path.join(HERE, "..", "..", "tasks", "pack-bind-retire"))
SEEDS = ("0", "1", "7", "12345", "99991")

SNIP = (
    "import sys, hashlib;"
    "sys.path.insert(0, %r);"
    "sys.path.insert(0, %r);"
    "import gen;"
    "from hst import ev;"
    "import tempfile, os;"
    "d = tempfile.mkdtemp();"
    "h = hashlib.sha256();"
    "rows = [];"
    "[ (open(os.path.join(d, 'c%%03d.txt' %% i), 'w').write(gen.spec(0x5EED ^ (i * 0x9E3779B1))),"
    "   h.update(open(os.path.join(d, 'c%%03d.txt' %% i)).read().encode()),"
    "   ev.go('c%%03d' %% i, os.path.join(d, 'c%%03d.txt' %% i), rows)) for i in range(120) ];"
    "print(h.hexdigest());"
    "print(hashlib.sha256('\\n'.join(rows).encode()).hexdigest())"
)


def tree(work):
    dest = os.path.join(work, "tree")
    shutil.copytree(os.path.join(TASK, "environment", "app_src"), dest)
    for f in sorted(os.listdir(os.path.join(TASK, "solution"))):
        if f.endswith(".py"):
            shutil.copyfile(os.path.join(TASK, "solution", f), os.path.join(dest, "hst", f))
    return dest


def main():
    work = tempfile.mkdtemp(prefix="dt-")
    t = tree(work)
    code = SNIP % (os.path.join(TASK, "tests"), t)
    seen = {}
    for s in SEEDS:
        env = dict(os.environ, PYTHONHASHSEED=s, PYTHONDONTWRITEBYTECODE="1")
        r = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, env=env)
        if r.returncode != 0:
            print("PYTHONHASHSEED=%s faulted:\n%s" % (s, r.stderr[-800:]))
            shutil.rmtree(work, ignore_errors=True)
            return 1
        seen[s] = tuple(r.stdout.split())
    shutil.rmtree(work, ignore_errors=True)
    vals = sorted(set(seen.values()))
    for s in SEEDS:
        print("PYTHONHASHSEED=%-6s scripts %s ledger %s" % (s, seen[s][0][:16], seen[s][1][:16]))
    if len(vals) != 1:
        print("the generator or the reference is not deterministic across processes")
        return 1
    print("120 scripts and their ledgers identical across %d hash seeds" % len(SEEDS))
    return 0


if __name__ == "__main__":
    sys.exit(main())
