"""The two-image trial, emulated on a host that has no docker.

What it does cover: the real `tests/runner.py`, driven in a subprocess out of a
work tree staged the way `tests/Dockerfile` stages it -- `pristine` beside
`tests/` rather than inside it, because the image moves it and a `cases.py`
that reads it through `tests/pristine` resolves on the authoring host and
raises inside the container. It grades with the real `tests/test_outputs.py`
under the real pytest, rather than re-implementing the comparison.

What it does NOT cover, and the handover has to say so: the privilege drop, the
root-owned reward channel, the root-only ground truth, `reap.py`, and every
integrity probe that needs a POSIX the host does not have. A probe that faults
because `os.fork` is missing has been rejected by nothing, so those are
reported as `skipped (host)` rather than as a pass.

    python3 authoring/trial.py --all
    python3 authoring/trial.py --variants
    python3 authoring/trial.py --only cheat-rule-merge-before-talk.sh

Each row prints as it is decided, so a harness that dies leaves evidence of how
far it got rather than an empty table that reads as a clean sweep.
"""
import argparse
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

TASK = pathlib.Path(__file__).resolve().parent.parent
ARTIFACTS = ("note/board.py", "note/rule.py")


def _bash():
    """A bare `bash` on Windows is the WSL launcher, which prints a notice and
    exits 1 having done nothing, so a harness that trusts it grades the shipped
    tree and reports that it graded a cheat. Prefer a real shell by path."""
    named = os.environ.get("NCF_BASH")
    if named:
        return named
    for path in (r"C:\Program Files\Git\bin\bash.exe",
                 r"C:\Program Files (x86)\Git\bin\bash.exe"):
        if os.path.isfile(path):
            return path
    found = shutil.which("bash")
    if not found:
        raise SystemExit("no bash on PATH; set NCF_BASH to one")
    return found


# test_outputs.py addresses the container's absolute paths. The emulation
# rewrites those three and nothing else, and asserts each one matched, so it
# cannot quietly grade a different file than the one that ships.
PATHS = (
    ('WORK = pathlib.Path("/work")', 'WORK = pathlib.Path(%s)'),
    ('TRUTH = pathlib.Path("/tests/gt.json")', 'TRUTH = pathlib.Path(%s)'),
    ('pristine = pathlib.Path("/pristine")', 'pristine = pathlib.Path(%s)'),
)


def stage(root):
    """Lay the tree out the way tests/Dockerfile lays it out."""
    shutil.copytree(TASK / "tests" / "pristine", root / "pristine")
    shutil.copytree(TASK / "tests", root / "tests",
                    ignore=shutil.ignore_patterns("pristine", "__pycache__"))
    shutil.copytree(TASK / "environment" / "app_src", root / "app",
                    ignore=shutil.ignore_patterns("__pycache__"))
    (root / "work").mkdir()
    grader = root / "tests" / "test_outputs.py"
    body = grader.read_text()
    for literal, shape in PATHS:
        if literal not in body:
            raise SystemExit("test_outputs.py no longer contains %r; the "
                             "emulation cannot claim to grade it" % literal)
        target = {"WORK": root / "work", "TRUTH": root / "tests" / "gt.json"}.get(
            literal.split(" ")[0], root / "pristine")
        body = body.replace(literal, shape % repr(str(target)), 1)
    grader.write_text(body, newline="\n")


def apply_subject(root, subject):
    """Put the submission into root/app, the way the agent container leaves it."""
    kind, ref = subject
    if kind == "nop":
        return
    if kind == "oracle":
        for rel in ARTIFACTS:
            shutil.copy(TASK / "solution" / pathlib.Path(rel).name, root / "app" / rel)
        return
    if kind == "variant":
        for rel in ARTIFACTS:
            src = TASK / "authoring" / "variants" / ref / pathlib.Path(rel).name
            if src.exists():
                shutil.copy(src, root / "app" / rel)
        return
    env = dict(os.environ, APP_DIR=str(root / "app"))
    done = subprocess.run([_bash(), str(TASK / "cheat" / ref)], env=env,
                          capture_output=True, text=True)
    if done.returncode != 0:
        # A playbook that never ran stages the shipped tree and scores 0 for a
        # reason that has nothing to do with the cheat.
        raise RuntimeError("cheat playbook exited %d: %s"
                           % (done.returncode, (done.stderr or done.stdout)[-400:]))


def run_once(root, seed, count):
    work = root / "work"
    shutil.rmtree(work)
    (work / "app").mkdir(parents=True)
    shutil.copytree(root / "pristine", work / "app", dirs_exist_ok=True,
                    ignore=shutil.ignore_patterns("__pycache__"))
    for rel in ARTIFACTS:
        live = root / "app" / rel
        if live.is_file():
            (work / "app" / rel).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy(live, work / "app" / rel)
    shutil.copy(root / "tests" / "scen.py", work / "scen.py")
    shutil.copy(root / "tests" / "runner.py", work / "runner.py")
    out = work / "out.json"
    out.write_text("")
    env = dict(os.environ, APPDIR=str(work / "app"), RUN_SEED=str(seed),
               RUN_COUNT=str(count), PYTHONPATH=str(work),
               PYTHONDONTWRITEBYTECODE="1")
    # The submission runs in its own interpreter, as it does in the container.
    # In process, a probe that calls os._exit takes the harness down with it and
    # the run reads as a clean sweep.
    driver = (
        "import os, runpy, sys\n"
        "fd = os.open(r'%s', os.O_WRONLY | os.O_TRUNC)\n"
        "os.environ['OUT_FD'] = str(fd)\n"
        "runpy.run_path(r'%s', run_name='__main__')\n" % (out, work / "runner.py"))
    subprocess.run([sys.executable, "-c", driver], env=env,
                   capture_output=True, text=True, timeout=1800)
    done = subprocess.run(
        [sys.executable, "-m", "pytest", str(root / "tests" / "test_outputs.py"),
         "-q", "-rf", "--tb=line"],
        cwd=str(root / "tests"), env=dict(env, PYTHONPATH=str(root / "tests")),
        capture_output=True, text=True, timeout=3600)
    blob = done.stdout + done.stderr
    fired = sorted(set(re.findall(r"(test_[a-z_]+)",
                                  "\n".join(l for l in blob.splitlines()
                                            if l.startswith("FAILED") or " - " in l))))
    return (1 if done.returncode == 0 else 0), fired, blob


def subjects(args):
    out = []
    if args.variants:
        for path in sorted((TASK / "authoring" / "variants").iterdir()):
            if path.is_dir():
                out.append((path.name, ("variant", path.name), 1))
        return out
    out.append(("solution (oracle)", ("oracle", None), 1))
    out.append(("no change (nop)", ("nop", None), 0))
    for path in sorted((TASK / "cheat").glob("*.sh")):
        out.append((path.name, ("cheat", path.name), 0))
    if args.only:
        out = [row for row in out if row[0] == args.only]
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--variants", action="store_true")
    ap.add_argument("--only")
    ap.add_argument("--seed", type=int, default=4242)
    ap.add_argument("--count", type=int, default=120)
    args = ap.parse_args()

    rows = subjects(args)
    bad = 0
    print("seed %d, %d generated streams a run\n" % (args.seed, args.count))
    for name, subject, want in rows:
        root = pathlib.Path(tempfile.mkdtemp(prefix="ncf-"))
        try:
            stage(root)
            try:
                apply_subject(root, subject)
            except RuntimeError as exc:
                print("  %-46s SKIPPED (host)  %s" % (name, exc))
                continue
            got, fired, blob = run_once(root, args.seed, args.count)
            mark = "ok " if got == want else "BAD"
            if got != want:
                bad += 1
            print("  %-46s reward %d want %d  %s  %s"
                  % (name, got, want, mark, ",".join(fired[:3])))
            if got != want:
                print("\n".join("        " + l for l in blob.splitlines()[-12:]))
        finally:
            shutil.rmtree(root, ignore_errors=True)
        sys.stdout.flush()
    print("\n%d of %d as expected, %d unexpected" % (len(rows) - bad, len(rows), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
