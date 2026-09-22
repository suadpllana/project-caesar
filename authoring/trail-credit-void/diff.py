"""Differential test: the reference, the sealed model and the naive families must agree.

Runs the generated population through each tree in a subprocess (so a module-level import
cannot leak state between them) and reports the first disagreement per pair. Output is the
measurement, so it is flushed.
"""
import json
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "trail-credit-void"

TREE = """
import json, sys, time
sys.path.insert(0, %(tests)r)
sys.path.insert(0, %(tree)r)
import gen, run_crd
work = gen.programs(%(seed)r, %(per)d)
if %(small)d:
    work = [w for w in work if w[0] not in ('wide', 'deep')]
got = {}
t0 = time.perf_counter()
for fam, name, lines in work:
    got[name] = run_crd.run("\\n".join(lines) + "\\n")
sys.stderr.write("%%.2f\\n" %% (time.perf_counter() - t0))
sys.stdout.write(json.dumps(got))
"""

SEAL = """
import json, sys, time
sys.path.insert(0, %(tests)r)
sys.path.insert(0, %(seal)r)
import gen, model
work = gen.programs(%(seed)r, %(per)d)
if %(small)d:
    work = [w for w in work if w[0] not in ('wide', 'deep')]
got = {}
t0 = time.perf_counter()
for fam, name, lines in work:
    got[name] = model.expect(lines)
sys.stderr.write("%%.2f\\n" %% (time.perf_counter() - t0))
sys.stdout.write(json.dumps(got))
"""


def run(src, **kw):
    kw.setdefault("tests", str(TASK / "tests"))
    kw.setdefault("seal", str(TASK / "tests" / "seal"))
    done = subprocess.run([sys.executable, "-c", src % kw], capture_output=True, text=True)
    if done.returncode != 0:
        print(done.stderr[-2000:], flush=True)
        raise SystemExit("subprocess failed")
    return json.loads(done.stdout), done.stderr.strip()


def main():
    seed = sys.argv[1] if len(sys.argv) > 1 else "diff-seed"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 40
    small = 1 if len(sys.argv) > 3 and sys.argv[3] == "small" else 0
    base, took = run(SEAL, seed=seed, per=per, small=small)
    print("model     %6s s   %d trails" % (took, len(base)), flush=True)
    for tree in ("ref", "slow-snap", "slow-sweep"):
        here = HERE / tree
        if not here.is_dir():
            continue
        got, took = run(TREE, tree=str(here), seed=seed, per=per, small=small)
        bad = [name for name in base if base[name] != got.get(name)]
        print("%-10s %6s s   %s" % (tree, took,
                                    "agrees" if not bad
                                    else "%d differ, first %s" % (len(bad), bad[:3])),
              flush=True)
        if bad:
            name = bad[0]
            want, have = base[name], got.get(name) or []
            for i in range(max(len(want), len(have))):
                a = want[i] if i < len(want) else "-"
                b = have[i] if i < len(have) else "-"
                if a != b:
                    print("   line %d  model %r  %s %r" % (i, a, tree, b), flush=True)
                    break


if __name__ == "__main__":
    main()
