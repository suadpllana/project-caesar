"""The host emulation: the real runner, the real grader, no container.

It stages the tree the way the verifier image builds it - `tests/` without
`pristine`, and the untouched copy beside it rather than inside it - because a
gate that runs against the authoring layout says nothing about the layout the
pipeline builds. It drives the submitted code in a child process, the way
`runner.py` is driven for real, so a probe that calls `os._exit` kills the child
and not the table. And it prints each row as it is decided, so a harness that
dies halfway leaves evidence of how far it got instead of looking like a clean
sweep.

What it does NOT cover, and this belongs in every handover that leans on it: the
privilege drop, the root-owned reward channel, the unreadable answers, and the
reaping of anything the run leaves behind. Those need the two images.

    python3 authoring/trial.py                 the reference and the shipped tree
    python3 authoring/trial.py --all           plus every cheat
    python3 authoring/trial.py --variants      every other correct reading
    python3 authoring/trial.py --count 60      fewer generated feeds, for speed
"""

import json
import os
import pathlib
import shutil
import subprocess
import sys
import tempfile

import lab

TESTS = lab.ROOT / "tests"
CHEAT = lab.ROOT / "cheat"
VAR = lab.ROOT / "authoring" / "variants"


def stage(hold, over):
    app = os.path.join(hold, "app")
    lab.tree(app, over)
    box = os.path.join(hold, "tests")
    shutil.copytree(TESTS, box,
                    ignore=shutil.ignore_patterns("pristine", "__pycache__",
                                                  "*.pyc"))
    shutil.copytree(TESTS / "pristine", os.path.join(hold, "pristine"),
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    return app, box


def playbook(app, script):
    """Apply a cheat the way test.sh would: it writes into the agent's /app."""
    run = subprocess.run(["bash", str(script)], capture_output=True, text=True,
                         env=dict(os.environ, APP_DIR=app), timeout=300)
    if run.returncode != 0:
        raise RuntimeError("%s exited %d: %s"
                           % (script.name, run.returncode, run.stderr[-600:]))


def grade(over, nonce, count, script=None, detail=False):
    hold = tempfile.mkdtemp(prefix="pcg-trial-")
    try:
        app, box = stage(hold, over)
        if script is not None:
            playbook(app, script)
        out = os.path.join(hold, "out.json")
        env = dict(os.environ, APPDIR=app, RUN_NONCE=nonce,
                   RUN_COUNT=str(count), PYTHONDONTWRITEBYTECODE="1")
        run = subprocess.run([sys.executable, os.path.join(box, "runner.py"), out],
                             capture_output=True, text=True, env=env, timeout=1800)
        if not os.path.exists(out):
            gone = "the run published nothing (%s)" % run.stderr[-300:]
            return (0, gone, ["no-report"]) if detail else (0, gone)
        env = dict(os.environ, RUN_OUT=out, APP_DIR=app,
                   PRISTINE_DIR=os.path.join(hold, "pristine"),
                   RUN_NONCE=nonce, RUN_COUNT=str(count),
                   PYTHONPATH=box, PYTHONDONTWRITEBYTECODE="1",
                   ALLOW_PROFILE="1")
        run = subprocess.run([sys.executable, "-m", "pytest", "-q", "--no-header", "-rf", "--tb=no",
                              os.path.join(box, "test_outputs.py")],
                             capture_output=True, text=True, env=env, timeout=1800)
        broke = []
        for line in run.stdout.splitlines():
            if line.startswith("FAILED "):
                node = line.split()[1]
                broke.append(node.split("::")[-1].split("[")[0])
        broke = sorted(set(broke))
        if run.returncode == 0:
            return (1, "all tests passed", []) if detail else (1, "all tests passed")
        note = ", ".join(broke) or run.stdout[-200:]
        return (0, note, broke) if detail else (0, note)
    finally:
        shutil.rmtree(hold, ignore_errors=True)


def row(label, want, got, note):
    mark = "ok " if got == want else "BAD"
    print("%s  %-34s reward %d (want %d)  %s" % (mark, label, got, want, note[:90]))
    sys.stdout.flush()
    return got == want


def main(argv):
    count = 120
    if "--count" in argv:
        count = int(argv[argv.index("--count") + 1])
    nonce = "trial-nonce"
    fine = True
    got, note = grade(lab.reference(), nonce, count)
    fine &= row("reference", 1, got, note)
    got, note = grade(lab.shipped(), nonce, count)
    fine &= row("shipped tree", 0, got, note)

    if "--variants" in argv or "--all" in argv:
        for d in sorted(p for p in VAR.iterdir() if p.is_dir()):
            over = dict(lab.reference())
            for f in sorted(d.glob("*.py")):
                over[f.name] = f.read_text()
            got, note = grade(over, nonce, count)
            fine &= row("variant " + d.name, 1, got, note)

    if "--all" in argv:
        for s in sorted(CHEAT.glob("*.sh")):
            try:
                got, note = grade(lab.shipped(), nonce, count, script=s)
            except RuntimeError as exc:
                got, note = -1, str(exc)
            fine &= row("cheat " + s.stem, 0, got, note)

    print("\n%s" % ("every trial landed where it should"
                    if fine else "SOMETHING IS WRONG ABOVE"))
    return 0 if fine else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
