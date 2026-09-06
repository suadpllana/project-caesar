"""Run every cheat through the verifier and say which test caught it.

A cheat suite that only reports "all scored 0" proves less than it looks. The attestation
probes each interfere with exactly one evidence layer, and the point of shipping them is
that the layer they attack is the layer that catches them - if `cheat-rebind-frozen` is
caught by the row comparison instead of by the fingerprint test, the fingerprint test is
decoration and nobody has noticed.

So this asserts three things: every cheat scores 0; each attestation probe is caught by its
own test; and no attestation probe is caught only by something else.

The sweep runs with the wide family reduced, because it is measuring semantics and
containment rather than the resource gate. The resource gate is measured on its own, by
`trial.py` at full width against the shipped naive scanners, and the numbers live in
`STATE.md`.

Usage:
    python3 authoring/token-seam-emit/cheat_report.py <task-dir>
"""
import os
import re
import shutil
import subprocess
import sys
import tempfile

# Which test each attestation probe has to be caught by.
OWNED = {
    "cheat-rebind-frozen": "test_frozen_entry_points_were_not_rebound",
    "cheat-patch-frozen-file": "test_executed_tree_matches_pristine_outside_the_declared_artifacts",
    "cheat-kill-monitor": "test_the_release_module_ran_for_every_row",
    "cheat-bypass-gate": "test_no_request_emitted_rows_it_was_not_asked_for",
}


def find_bash():
    """The POSIX bash, not the one Windows resolves to.

    On Windows `bash` on PATH is the WSL launcher, which has no distribution installed and
    fails every cheat script with a message about Linux. The authoring shell is Git Bash,
    so look there first.
    """
    for p in (os.environ.get("TSE_BASH"),
              "C:/Program Files/Git/bin/bash.exe",
              "C:/Program Files/Git/usr/bin/bash.exe"):
        if p and os.path.isfile(p):
            return p
    return "bash"


BASH = find_bash()


def build_app(task, script, work):
    """Run one cheat script against a copy of the shipped tree and return that tree."""
    app = os.path.join(work, "app")
    shutil.rmtree(app, ignore_errors=True)
    shutil.copytree(os.path.join(task, "environment", "app_src"), app)
    env = dict(os.environ)
    # bash reads a backslash as an escape, so both paths go over in posix form.
    env["APP"] = app.replace("\\", "/")
    r = subprocess.run([BASH, script.replace("\\", "/")],
                       capture_output=True, text=True, env=env)
    if r.returncode != 0:
        return None, ((r.stderr or r.stdout).strip() or "rc=%d" % r.returncode)
    return app, ""


def main(argv):
    # forgecheck runs this with no arguments and the task directory as the cwd, so an
    # absent argument means "the task I am standing in" rather than "explain yourself".
    task = os.path.abspath(argv[0] if argv else os.getcwd())
    if not os.path.isfile(os.path.join(task, "task.toml")):
        print(__doc__)
        return 2
    cheats = sorted(f for f in os.listdir(os.path.join(task, "cheat"))
                    if f.endswith(".sh"))
    work = tempfile.mkdtemp(prefix="tse-cheats-")

    bad = []
    print("%-34s %6s  %s" % ("cheat", "reward", "caught by"))
    for name in cheats:
        app, err = build_app(task, os.path.join(task, "cheat", name), work)
        if app is None:
            print("%-34s %6s  script failed: %s" % (name, "-", err[:60]))
            bad.append("%s: script failed" % name)
            continue
        r = subprocess.run(
            [sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                          "trial.py"),
             task, "--agent", app, "--wide", "0", "--nonce", "cheatsweep"],
            capture_output=True, text=True)
        out = r.stdout
        reward = 1 if re.search(r"^\s*reward\s+1\s*$", out, re.M) else 0
        caught = sorted(set(re.findall(r"FAILED .*::(\w+)", out)))
        if not caught and reward == 0:
            caught = ["run did not complete"]
        print("%-34s %6d  %s" % (name[:-3], reward, ", ".join(caught) or "-"))

        stem = name[:-3]
        if reward != 0:
            bad.append("%s scored 1" % stem)
        owner = OWNED.get(stem)
        if owner is not None:
            if owner not in caught:
                bad.append("%s was not caught by %s" % (stem, owner))
            others = [c for c in caught if c != owner and c != "run did not complete"]
            if not caught:
                bad.append("%s was not caught at all" % stem)
            elif others and owner not in caught:
                bad.append("%s was caught only by %s" % (stem, ", ".join(others)))

    shutil.rmtree(work, ignore_errors=True)
    print()
    if bad:
        for b in bad:
            print("FINDING %s" % b)
        return 1
    print("%d cheats, every one scored 0, every attestation probe caught by its own layer"
          % len(cheats))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
