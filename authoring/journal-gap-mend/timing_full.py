"""Time correct implementations over a full-size graded set: every hand journal plus the
generator at the graded count, one process per implementation, as the worker runs them.

    python3 authoring/journal-gap-mend/timing_full.py <seed> [dir ...]

The limit in the brief is 120 s for the whole set; this is what it is validated against
(docs/INSTRUCTION-CONTRACT.md: a limit is validated with a second, independently written
implementation, never only the reference). The sealed model is timed too.
"""
import pathlib
import subprocess
import sys
import time

sys.dont_write_bytecode = True  # never leave __pycache__ inside the bundle

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "journal-gap-mend"

RUN = r'''
import sys, time, pathlib
sys.path.insert(0, %(here)r)
import readings
readings._sealed()
import cases, gen, model
texts = [cases.text(n) for n in cases.ORDER] + [t for _f, _n, t in gen.programs(%(seed)r, 30)]
which = %(which)r
t0 = time.time()
if which == "model":
    for t in texts:
        model.expect(t)
else:
    app = readings._overlay(which)
    mend = readings._fresh(app)
    for t in texts:
        mend.run(t)
print("%%d journals %%.2f s" %% (len(texts), time.time() - t0))
'''


def main(argv):
    seed = argv[0]
    dirs = argv[1:] or [str(TASK / "solution"), str(HERE / "variants" / "topdown"),
                        str(HERE / "variants" / "packed"), "model"]
    for d in dirs:
        code = RUN % {"here": str(HERE), "seed": seed, "which": d}
        proc = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True)
        print("%-60s %s" % (d.replace(str(HERE.parents[1]) + "/", ""),
                            (proc.stdout.strip() or proc.stderr.strip()[-200:])), flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
