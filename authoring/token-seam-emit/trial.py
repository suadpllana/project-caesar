"""Host emulation of the verifier, for a machine with no Docker.

It runs the same four stages `tests/test.sh` runs, in the same order, against the same
files: lay the pristine tree with the declared artifacts over it, generate the graded
requests from a nonce, run them under the assembled tree, then grade with pytest.

WHAT THIS DOES NOT COVER, and the handover has to say so: the image builds, artifact upload
into the verifier container, the privilege drop to an unprivileged uid, `setsid --wait`,
the wall-clock kill, and `reap.py` walking /proc. Everything those protect against is
untested here. A green run means "not failing for a reason this host can see", never "will
pass".

Usage:
    python3 authoring/token-seam-emit/trial.py <task-dir> --agent reference|shipped|<dir>
"""
import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import time


def stage(label, argv, env=None):
    t0 = time.time()
    r = subprocess.run(argv, capture_output=True, text=True, env=env)
    secs = time.time() - t0
    ok = r.returncode == 0
    print("  %-9s %-4s %6.1fs  %s" % (label, "ok" if ok else "FAIL", secs,
                                      (r.stdout or r.stderr).strip().splitlines()[-1:] or ""))
    return ok, r


def agent_tree(task, which, work):
    """The /app the verifier would see.

    `which` is "shipped", "reference", a directory holding the four modules, or a whole app
    tree. The last case is the one the cheat sweep hands over, and getting it wrong is not
    hypothetical: an earlier version listed the tree's top level for *.py, found only
    run_stream.py, and copied that into strm/, so every cheat was silently graded as the
    shipped tree and every one of them "scored 0" for the wrong reason.
    """
    tree = os.path.join(work, "app")
    shutil.copytree(os.path.join(task, "environment", "app_src"), tree)
    if which == "shipped":
        return tree
    src = os.path.join(task, "solution") if which == "reference" else which
    if os.path.isdir(os.path.join(src, "strm")):
        src = os.path.join(src, "strm")
    found = [f for f in sorted(os.listdir(src)) if f.endswith(".py")]
    wanted = [f for f in found if f in ("sm.py", "hb.py", "rel.py", "fin.py")]
    if not wanted:
        raise SystemExit("no editable modules found in %s (saw %s)" % (src, found))
    for f in wanted:
        shutil.copy(os.path.join(src, f), os.path.join(tree, "strm", f))
    return tree


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("task")
    ap.add_argument("--agent", default="reference")
    ap.add_argument("--nonce", default=None)
    ap.add_argument("--keep", action="store_true")
    ap.add_argument("--wide", default=None)
    a = ap.parse_args(argv)

    task = os.path.abspath(a.task)
    tests = os.path.join(task, "tests")
    # Scratch never lands inside the bundle: package.py ships what it finds, and a
    # previous run's .trial/ put 370 stray files in the zip.
    work = tempfile.mkdtemp(prefix="tse-trial-")
    lab = os.path.join(work, "lab")
    os.makedirs(os.path.join(lab, "out"))
    nonce = a.nonce or ("host-%d" % int(time.time()))

    print("trial: agent=%s nonce=%s" % (a.agent, nonce))
    app = agent_tree(task, a.agent, work)

    ok, _ = stage("lay", [sys.executable, os.path.join(tests, "lay.py"),
                          "--pristine", os.path.join(tests, "pristine"),
                          "--agent", app, "--into", os.path.join(lab, "tree")])
    if not ok:
        return 2
    mkenv = dict(os.environ)
    if a.wide is not None:
        mkenv["TSE_WIDE"] = str(a.wide)
    ok, _ = stage("mkcases", [sys.executable, os.path.join(tests, "mkcases.py"),
                              "--nonce", nonce, "--into", os.path.join(lab, "req")],
                  env=mkenv)
    if not ok:
        return 2
    stage("run", [sys.executable, os.path.join(tests, "runner.py"),
                  os.path.join(lab, "tree"), os.path.join(lab, "req"),
                  os.path.join(lab, "out", "rows.txt")])

    env = dict(os.environ)
    env["LAB"] = lab
    env["PRISTINE"] = os.path.join(tests, "pristine")
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    ok, r = stage("pytest", [sys.executable, "-m", "pytest", "-q",
                             os.path.join(tests, "test_outputs.py")], env=env)
    reward = 1 if ok else 0
    print("  reward    %d" % reward)
    if not ok:
        tail = [l for l in r.stdout.splitlines() if l.strip()][-18:]
        print("\n".join("    " + l for l in tail))
    if not a.keep:
        shutil.rmtree(work, ignore_errors=True)
    return 0 if reward else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
