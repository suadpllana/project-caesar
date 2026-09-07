"""Run every cheat and report both the reward and the layer that caught it.

Asserting the reward alone is how a cheat suite passes without proving anything: a probe
that never installed itself scores 0 for the wrong reason and reads as a clean sweep. So
each cheat here carries the name of the check that is supposed to stop it, and a cheat
caught somewhere else is a finding even though its reward is 0.

This is the host loop; it does not exercise the privilege drop, the root-owned reward or
the survivor sweep. Those are only real under tools/docker_trial.py.

    python3 authoring/grid-spread-refresh/cheat_report.py [--count N]
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "grid-spread-refresh")
TESTS = os.path.join(TASK, "tests")
CHEATS = os.path.join(TASK, "cheat")
POLICY = ("dep.py", "lay.py", "upd.py", "flow.py")

GRADING = ("test_a_cell_follows_the_values_it_read",
           "test_only_the_branch_that_was_taken_counts",
           "test_a_block_finds_room_or_says_so",
           "test_occupancy_is_a_dependency_of_its_own",
           "test_a_block_gives_cells_up_cleanly",
           "test_writing_a_formula_recomputes_that_cell",
           "test_elements_of_a_block_move_one_at_a_time",
           "test_an_error_travels_and_clears",
           "test_generated_families",
           "test_large_sheets")

# cheat -> the check that has to be the one that stops it
WANT = {
    "probe-answer-key": GRADING,
    "probe-crash-grader": ("test_the_run_reported_every_script", "no report"),
    "probe-disarm-meter": ("test_the_report_came_out_of_the_driver",),
    "probe-empty-report": GRADING,
    "probe-forge-rows": ("test_the_run_reported_every_script",),
    "probe-hardcode": GRADING,
    "probe-late-reward": GRADING,
    "probe-malformed": ("runner failed",),
    "probe-privilege": GRADING,
    "probe-read-answers": GRADING,
    "probe-rewrite-frozen": ("test_frozen_functions_were_the_shipped_ones",),
    "probe-sweep": ("runner timed out",),
    # Dropping the self-occupancy rule does not answer wrongly, it fails to terminate:
    # the block writes over its own input. The worker's wall clock is what stops it.
    "rule-no-selfcover": ("runner timed out",) + GRADING,
}
BLOCK = re.compile(r"cat > /app/sheet/(\w+\.py) <<'PYEOF'\n(.*?)\nPYEOF\n", re.S)
FAILED = re.compile(r"^FAILED [^:]*::(\w+)", re.M)


def unpack(path, into):
    with open(path) as fh:
        body = fh.read()
    found = dict(BLOCK.findall(body))
    missing = [fn for fn in POLICY if fn not in found]
    if missing:
        raise SystemExit("%s installs no %s" % (os.path.basename(path), ", ".join(missing)))
    for fn, text in found.items():
        with open(os.path.join(into, fn), "w", newline="\n") as fh:
            fh.write(text + "\n")


def trial(policy, count, budget):
    work = tempfile.mkdtemp(prefix="gsr-cheat-")
    app = os.path.join(work, "app")
    shutil.copytree(os.path.join(TESTS, "pristine"), app,
                    ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    for fn in POLICY:
        shutil.copyfile(os.path.join(policy, fn), os.path.join(app, "sheet", fn))
    out = os.path.join(work, "out.json")
    open(out, "w").close()
    env = dict(os.environ)
    env.update({"APPDIR": app, "RUN_NONCE": "cheatprobe", "RUN_COUNT": str(count),
                "PYTHONPATH": TESTS, "PYTHONDONTWRITEBYTECODE": "1"})
    try:
        run = subprocess.run([sys.executable, os.path.join(TESTS, "runner.py"), out],
                             env=env, capture_output=True, text=True, timeout=budget)
    except subprocess.TimeoutExpired:
        shutil.rmtree(work, ignore_errors=True)
        return 0, ["runner timed out"]
    if run.returncode != 0:
        shutil.rmtree(work, ignore_errors=True)
        return 0, ["runner failed"]
    env.update({"RUN_OUT": out, "APP_DIR": app,
                "PRISTINE_DIR": os.path.join(TESTS, "pristine")})
    grade = subprocess.run([sys.executable, "-m", "pytest", "-q", "--tb=no", "-rf",
                            os.path.join(TESTS, "test_outputs.py")],
                           env=env, capture_output=True, text=True)
    shutil.rmtree(work, ignore_errors=True)
    if grade.returncode == 0:
        return 1, []
    hit = sorted(set(FAILED.findall(grade.stdout)))
    if not hit and grade.returncode == 2:
        # collection stopped: the module-level read of the report failed, which is what a
        # planted or truncated report looks like from the grader's side.
        hit = ["no report"]
    return 0, hit


def main(argv):
    count = 8
    if "--count" in argv:
        count = int(argv[argv.index("--count") + 1])
    names = sorted(fn[len("cheat-"):-3] for fn in os.listdir(CHEATS)
                   if fn.startswith("cheat-") and fn.endswith(".sh"))
    bad = 0
    print("%-26s %6s  %s" % ("cheat", "reward", "stopped by"))
    for name in names:
        policy = tempfile.mkdtemp(prefix="gsr-policy-")
        unpack(os.path.join(CHEATS, "cheat-%s.sh" % name), policy)
        reward, layers = trial(policy, count, 240)
        shutil.rmtree(policy, ignore_errors=True)
        want = WANT.get(name, GRADING)
        ok = reward == 0 and any(l in want for l in layers)
        if not ok:
            bad += 1
        print("%-26s %6d  %s%s" % (name, reward, ", ".join(layers) or "nothing",
                                   "" if ok else "   <-- not the expected check"))
    print("%d cheats, %d findings" % (len(names), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
