"""Time the reference and each naive-but-correct family on one program, under the task caps.

Output is the measurement, so everything flushes.
"""
import pathlib
import resource
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

CAP_MB = 2048


def limit():
    resource.setrlimit(resource.RLIMIT_AS, (CAP_MB * 1024 * 1024,) * 2)


def one(name, over, prog, cap):
    here = lab.tree(lab.TASK / "solution", over)
    t = time.time()
    try:
        out = subprocess.run(
            [sys.executable, str(here / "run_tab.py"), str(prog)],
            capture_output=True, text=True, timeout=cap, cwd=str(here),
            preexec_fn=limit)
    except subprocess.TimeoutExpired:
        print("%-10s over %d s" % (name, cap), flush=True)
        return
    spent = time.time() - t
    if out.returncode != 0:
        tail = out.stderr.strip().splitlines()[-1:] or [""]
        print("%-10s %6.1f s  failed: %s" % (name, spent, tail[0][:90]), flush=True)
        return
    print("%-10s %6.1f s  %d lines" % (name, spent, len(out.stdout.splitlines())), flush=True)


if __name__ == "__main__":
    prog = sys.argv[1]
    cap = int(sys.argv[2]) if len(sys.argv) > 2 else 400
    one("reference", None, prog, cap)
    for name in ("scan", "perkey", "copy"):
        one(name, HERE / "slow" / name, prog, cap)
