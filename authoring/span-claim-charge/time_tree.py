"""Sweep the tree family's shape: the reference, the family walk and the standing-set table.

Output is the measurement, so everything flushes. Arguments: stamps writes asks [seed].
"""
import pathlib
import random
import subprocess
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
import gen  # noqa: E402


def one(name, over, prog, cap):
    here = lab.tree(lab.TASK / "solution", over)
    t = time.time()
    try:
        out = subprocess.run([sys.executable, str(here / "run_store.py"), str(prog)],
                             capture_output=True, text=True, timeout=cap, cwd=str(here))
    except subprocess.TimeoutExpired:
        print("   %-10s over %d s" % (name, cap), flush=True)
        return None
    spent = time.time() - t
    if out.returncode != 0:
        print("   %-10s failed: %s" % (name, out.stderr.strip().splitlines()[-1][:90]), flush=True)
        return None
    print("   %-10s %6.1f s" % (name, spent), flush=True)
    return out.stdout


def main():
    gen.TREE_STAMPS, gen.TREE_WRITES, gen.TREE_ASKS = int(sys.argv[1]), int(sys.argv[2]), int(sys.argv[3])
    seed = sys.argv[4] if len(sys.argv) > 4 else "sweep"
    rows = gen.MAKE["tree"](random.Random(seed))
    print("stamps=%d writes=%d asks=%d: %d lines, %d u" % (
        gen.TREE_STAMPS, gen.TREE_WRITES, gen.TREE_ASKS, len(rows),
        sum(1 for r in rows if r.startswith("u "))), flush=True)
    room = pathlib.Path(tempfile.mkdtemp(prefix="scc-tree-"))
    prog = room / "tree.txt"
    prog.write_text("\n".join(rows) + "\n", encoding="utf-8", newline="\n")
    got = {}
    got["reference"] = one("reference", None, prog, 600)
    got["keys"] = one("keys", HERE / "slow" / "keys", prog, 600)
    got["walk"] = one("walk", HERE / "slow" / "family", prog, 600)
    for k in ("keys", "walk"):
        if got[k] is not None and got[k] != got["reference"]:
            print("   %s DISAGREES with the reference" % k, flush=True)


if __name__ == "__main__":
    main()
