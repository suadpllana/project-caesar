"""What each wrong reading costs, measured on the graded population and on the hand cases.

Two numbers per reading, and the second is the one that matters. The share of generated
programs it gets wrong says whether the population is shaped for it at all - grading is all or
nothing, so a reading that moves one program in three hundred still scores 0, but a reading
that moves none is a reading nothing tests. The named case says which enumerated program
catches it, and a reading no case catches is a rule the fixed set does not fence.

This file is also the module `tools/readingcheck.py` reads, so the two measurements come from
one set of engines rather than from two that can drift apart: REFERENCE, READINGS, run(),
enumerated() and generated() are its contract, and main() is the report.

    python authoring/bind-claim-prune/readings.py [<per>]
    python tools/readingcheck.py bind-claim-prune
"""
import json
import pathlib
import shutil
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import lab  # noqa: E402

TASK = lab.TASK
KIDS = HERE / "readings"
PARTS = ("hold.py", "want.py", "pull.py", "place.py", "prune.py", "wire.py")

sys.path.insert(0, str(TASK / "tests"))

REFERENCE = str(TASK / "solution")


def _readings():
    """Each reading as the files it replaces in the reference - only the ones it changed."""
    out = {}
    for room in sorted(p for p in KIDS.iterdir() if p.is_dir()):
        files = {}
        for name in PARTS:
            mine = (room / name).read_text(encoding="utf-8")
            if mine != (pathlib.Path(REFERENCE) / name).read_text(encoding="utf-8"):
                files[name] = mine
        if not files:
            raise SystemExit("%s is byte-identical to the reference" % room.name)
        out[room.name] = files
    return out


READINGS = _readings()

ONE = HERE / "_one.py"
ONE_SRC = '''
import json, sys
app, prog = sys.argv[1], sys.argv[2]
sys.path.insert(0, app)
import ops
from bind import book
job = book.Job()
try:
    for line in open(prog, encoding="utf-8"):
        word = line.split()
        if word:
            ops.ex(job, tuple(word))
    print(json.dumps(job.out))
except Exception as exc:
    print(json.dumps(["RAISED %s" % type(exc).__name__]))
'''

_TREES = {}
_SEEN = {}


def _tree(policy):
    key = str(policy)
    if key not in _TREES:
        _TREES[key] = lab.tree(key)
    return _TREES[key]


def run(policy, text):
    """One program under one policy directory, as the lines it prints."""
    key = (str(policy), text)
    if key in _SEEN:
        return _SEEN[key]
    if not ONE.is_file():
        ONE.write_text(ONE_SRC, encoding="utf-8", newline="\n")
    app = _tree(policy)
    prog = pathlib.Path(app).parent / "prog.txt"
    prog.write_text(text if text.endswith("\n") else text + "\n", encoding="utf-8",
                    newline="\n")
    got = subprocess.run([sys.executable, str(ONE), str(app), str(prog)],
                         capture_output=True, text=True, timeout=300)
    out = json.loads(got.stdout.strip().splitlines()[-1]) if got.stdout.strip() else None
    _SEEN[key] = out
    return out


def enumerated():
    import cases
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    import gen
    out = []
    for fam, name, lines in gen.programs("readingcheck", max(1, n // 10)):
        if fam in ("wide", "deep"):
            continue
        out.append((name, "\n".join(lines)))
    return out[:n]


CHILD = r'''
import json, pathlib, sys
app, tests, seal, per = sys.argv[1], sys.argv[2], sys.argv[3], int(sys.argv[4])
sys.path.insert(0, app)
sys.path.insert(0, tests)
sys.path.insert(0, seal)
import ops
from bind import book
import cases, gen, model

def run(lines):
    job = book.Job()
    try:
        for line in lines:
            w = line.split()
            if w:
                ops.ex(job, tuple(w))
    except Exception as exc:
        return ["RAISED %s" % type(exc).__name__]
    return job.out

hit = []
for name in cases.ORDER:
    if run(cases.ops(name)) != model.expect(cases.ops(name)):
        hit.append(name)
bad = 0
seen = 0
for fam, name, lines in gen.programs("readings", per):
    if fam in ("wide", "deep"):
        continue
    seen += 1
    if run(lines) != model.expect(lines):
        bad += 1
print(json.dumps({"cases": hit, "bad": bad, "seen": seen}))
'''


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 30
    kid = HERE / "_child.py"
    kid.write_text(CHILD, encoding="utf-8", newline="\n")
    rows = []
    for name in sorted(READINGS):
        app = lab.tree(str(KIDS / name))
        got = subprocess.run(
            [sys.executable, str(kid), str(app), str(TASK / "tests"),
             str(TASK / "tests" / "seal"), str(per)],
            capture_output=True, text=True, timeout=1800)
        shutil.rmtree(app.parent, ignore_errors=True)
        if got.returncode != 0:
            print("%-16s CRASHED\n%s" % (name, got.stderr[-800:]))
            rows.append((name, -1.0, []))
            continue
        d = json.loads(got.stdout.strip().splitlines()[-1])
        rows.append((name, 100.0 * d["bad"] / max(d["seen"], 1), d["cases"]))
    kid.unlink()

    print("%-16s %7s  %s" % ("reading", "% wrong", "enumerated cases that catch it"))
    loose = []
    quiet = []
    for name, share, hit in rows:
        print("%-16s %6.1f%%  %s" % (name, share, ", ".join(hit[:4]) or "NONE"))
        if not hit:
            loose.append(name)
        if 0 <= share < 1.0:
            quiet.append(name)
    if loose:
        print("\nNO ENUMERATED CASE CATCHES: %s" % ", ".join(loose))
    if quiet:
        print("POPULATION BARELY MOVES FOR: %s" % ", ".join(quiet))
    return 1 if loose else 0


if __name__ == "__main__":
    sys.exit(main())
