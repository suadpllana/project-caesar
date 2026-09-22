"""Time each implementation on the wide trails, and check they agree line for line.

Run `python mk_scale.py scale` first: the trails it times are written there rather than kept,
because they are 2.5 MB of regenerable data and the shipped copies live in the task tree.

Output is the measurement, so everything is flushed (CLAUDE.md, 2026-09-09: buffered stdout
looks exactly like a hang).
"""
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
RUN = """
import sys, time
sys.path.insert(0, %r)
import run_crd
text = open(%r, encoding='utf-8').read()
t0 = time.perf_counter()
lines = run_crd.run(text)
took = time.perf_counter() - t0
sys.stderr.write('%%.3f %%d\\n' %% (took, len(lines)))
sys.stdout.write('\\n'.join(lines))
"""


def once(tree, trail):
    got = subprocess.run([sys.executable, "-c", RUN % (str(HERE / tree), str(trail))],
                         capture_output=True, text=True)
    if got.returncode != 0:
        return None, None, got.stderr.strip()[-300:]
    took, count = got.stderr.strip().split()
    return got.stdout, float(took), int(count)


def main():
    trees = sys.argv[1:] or ["ref", "slow-snap", "slow-sweep"]
    for name in ("wide.txt", "deep.txt"):
        trail = HERE / "scale" / name
        base = None
        print("== %s (%d bytes)" % (name, trail.stat().st_size), flush=True)
        for tree in trees:
            out, took, count = once(tree, trail)
            if out is None:
                print("   %-12s FAILED %s" % (tree, count), flush=True)
                continue
            same = "-" if base is None else ("same" if out == base else "DIFFERS")
            if base is None:
                base = out
            print("   %-12s %8.2f s   %6d lines   %s" % (tree, took, count, same),
                  flush=True)


if __name__ == "__main__":
    main()
