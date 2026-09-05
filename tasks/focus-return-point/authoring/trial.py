"""Host emulation of tests/test.sh: stage the tree the way the verifier does, run the real
runner and the real grader, read the verdict.

What it covers: the runner, the sink, the tally, the digests, the tree hash, the model
comparison and every graded assertion. What it does NOT cover: the privilege drop, the
root-only reward channel and answer files, setsid/timeout, and reap.py. Those need the
two-image trial (tools/docker_trial2.py), and the handover has to say which of the two
produced any number it quotes.

Usage:
    python3 authoring/trial.py oracle | nop | cheat/<file>.sh | --all | --variants
    python3 authoring/trial.py --dir <policy directory>
"""

import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.dirname(HERE)
APP = os.path.join(TASK, "environment", "app_src")
TESTS = os.path.join(TASK, "tests")
POL = ("focus.py", "keep.py", "reach.py", "mem.py")
COUNT = int(os.environ.get("RUN_COUNT", "300"))


def files_from_script(path):
    """The editable files a cheat script writes, read back out of its heredocs."""
    text = open(path).read()
    out = {}
    for m in re.finditer(r"cat > /app/ui/(\w+\.py) <<'PYEOF'\n(.*?)\nPYEOF\n", text, re.S):
        out[m.group(1)] = m.group(2) + "\n"
    return out


def files_from_dir(d):
    return {n: open(os.path.join(d, n)).read() for n in POL if os.path.isfile(os.path.join(d, n))}


def grade(files, label, want, keep=False):
    root = tempfile.mkdtemp(prefix="frp-trial-")
    work = os.path.join(root, "work")
    app = os.path.join(work, "app")
    tests = os.path.join(root, "tests")
    pristine = os.path.join(root, "pristine")
    shutil.copytree(APP, app, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    shutil.copytree(TESTS, tests, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", "pristine"))
    shutil.copytree(os.path.join(TESTS, "pristine"), pristine,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for n, src in files.items():
        with open(os.path.join(app, "ui", n), "w") as fh:
            fh.write(src)
    os.makedirs(os.path.join(work, "run"))
    out = os.path.join(work, "run", "out.json")
    nonce = os.urandom(12).hex()
    env = dict(os.environ, APPDIR=app, RUN_NONCE=nonce, RUN_COUNT=str(COUNT),
               PYTHONDONTWRITEBYTECODE="1", PYTHONPATH=tests, HOME=root, TMPDIR=root)
    try:
        subprocess.run([sys.executable, os.path.join(tests, "runner.py"), out],
                       env=env, timeout=600, capture_output=True, text=True)
    except subprocess.TimeoutExpired:
        print("    runner timed out")
    if not os.path.exists(out):
        open(out, "w").close()
    # The verifier image is 3.12 and test.sh insists on sys.monitoring; an older host
    # interpreter only has the profile hook, so the insistence is dropped here and the
    # two-image trial is where that flag is exercised.
    env.update(RUN_OUT=out, APP_DIR=app, PRISTINE_DIR=pristine,
               REQUIRE_MONITORING="1" if hasattr(sys, "monitoring") else "0")
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-rA", "--no-header",
                           "-p", "no:cacheprovider", os.path.join(tests, "test_outputs.py")],
                          env=env, capture_output=True, text=True, cwd=root)
    reward = 1 if proc.returncode == 0 else 0
    fails = [ln.split("::")[-1].split(" ")[0] for ln in proc.stdout.splitlines()
             if ln.startswith("FAILED")]
    reason = ""
    for ln in proc.stdout.splitlines():
        if ln.startswith("FAILED"):
            reason = ln.split(" - ", 1)[1][:110] if " - " in ln else ""
            break
    ok = reward == want
    print("%-44s reward=%d want=%d %s  %s%s" % (
        label, reward, want, "PASS" if ok else "FAIL",
        ",".join(fails[:3]) if fails else "", ("  " + reason) if reason else ""))
    if keep:
        print("    kept:", root)
    else:
        shutil.rmtree(root, ignore_errors=True)
    return ok, fails


def main(argv):
    what = argv[1] if len(argv) > 1 else "--all"
    if what == "oracle":
        return 0 if grade(files_from_dir(os.path.join(TASK, "solution")), "oracle", 1)[0] else 1
    if what == "nop":
        return 0 if grade({}, "nop", 0)[0] else 1
    if what == "--dir":
        return 0 if grade(files_from_dir(argv[2]), argv[2], 1)[0] else 1
    if what == "--variants":
        vd = os.path.join(HERE, "variants")
        res = [grade(files_from_dir(os.path.join(vd, d)), "variant " + d, 1)[0]
               for d in sorted(os.listdir(vd)) if d.startswith("ok-")]
        print("%d/%d variants scored 1" % (sum(res), len(res)))
        return 0 if all(res) else 1
    if what == "--all":
        res = [grade(files_from_dir(os.path.join(TASK, "solution")), "oracle", 1)[0],
               grade({}, "nop", 0)[0]]
        cd = os.path.join(TASK, "cheat")
        for f in sorted(os.listdir(cd)):
            if f.endswith(".sh"):
                res.append(grade(files_from_script(os.path.join(cd, f)), f, 0)[0])
        print("%d/%d trials behaved as required" % (sum(res), len(res)))
        return 0 if all(res) else 1
    return 0 if grade(files_from_script(what), os.path.basename(what), 0)[0] else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
