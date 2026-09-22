"""Would each isolation probe score 1 if the defence it attacks were missing?

A probe that scores 0 against the real verifier proves nothing unless it would have scored 1
without the defence (CLAUDE.md: assert the layer, never just the reward). This builds a weakened
copy of the verifier image - the worker runs as root, the sealed model stays readable, the
verdict directory is left open and no survivor is reaped - and runs the probes against it. The
real image is left alone; the weakened one is tagged apart and never ships.

test.sh is started from /work, a directory the worker can write, as a platform might start it.
The reward is read one second after test.sh returns, as a harness that collects it a moment
later would, so a survivor that keeps rewriting it gets the chance it would have in practice.

With --real the same probes run against the real verifier image, and the markers they leave
in /work name the layer that stopped them.

usage: python3 authoring/stale-line-spin/potency.py [--real] [probe ...]
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import docker_trial  # noqa: E402

WEAK = "stale-line-spin-test:weak"
PROBES = ("probe-answer-key", "probe-privilege", "probe-late-reward", "probe-disarm-grader",
          "probe-plant-report", "probe-shrink-set", "probe-cwd-plant")

# each edit removes one defence; each must fire exactly once or the experiment is void
EDITS = (
    ('chmod 0700 "${VERDICT}"', 'chmod 0777 "${VERDICT}"'),
    ('chmod 0700 /tests/seal', 'chmod 0755 /tests/seal'),
    ('setpriv --reuid="${RUNNER_ID}" --regid="${RUNNER_ID}" --clear-groups \\\n  ', ''),
    ('python3 -I /tests/reap.py || true', 'true'),
    ('\ncd /tests\n', '\n'),
    ('python3 -I -m pytest', 'python3 -m pytest'),
)


def weak_image():
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="sls-weak-"))
    try:
        ctx = tmp / "tests"
        shutil.copytree(ROOT / "tasks" / "stale-line-spin" / "tests", ctx)
        sh = ctx / "test.sh"
        text = sh.read_text()
        for old, new in EDITS:
            assert text.count(old) == 1, "defence not found: %r" % old
            text = text.replace(old, new)
        sh.write_text(text, newline="\n")
        df = ctx / "Dockerfile"
        d = df.read_text()
        assert d.count("chmod 0700 /tests/seal") == 1
        df.write_text(d.replace("chmod 0700 /tests/seal", "chmod 0755 /tests/seal"))
        built = docker_trial.local_context(ctx, tmp / "ctx")
        p = subprocess.run(["docker", "build", "-q", "-t", WEAK, str(built)],
                           capture_output=True, text=True)
        if p.returncode != 0:
            raise SystemExit(p.stderr[-2000:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def run(trial, name, image):
    tmp = pathlib.Path(tempfile.mkdtemp(prefix="sls-pot-"))
    try:
        trial.agent_run(trial.task / "cheat" / ("cheat-%s.sh" % name), tmp / "art")
        cmd = ("mkdir -p /app/sim ; cp -a /artifacts/. /app/ 2>/dev/null ; "
               "cd /work && bash /tests/test.sh > /tmp/v.log 2>&1 ; sleep 1 ; "
               "echo REWARD=$(cat /logs/verifier/reward.txt 2>/dev/null) ; "
               "grep -E 'passed|failed|error' /tmp/v.log | tail -1 ; "
               "cat /work/probe-*.txt 2>/dev/null")
        p = subprocess.run(["docker", "run", "--rm", "-v", "%s:/artifacts:ro" % (tmp / "art"),
                            image, "bash", "-c", cmd], capture_output=True, text=True)
        return p.stdout.strip().replace("\n", " | ")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    real = "--real" in sys.argv
    names = [a for a in sys.argv[1:] if a != "--real"] or PROBES
    trial = docker_trial.Trial("stale-line-spin")
    if not real:
        weak_image()
    image = trial.test_img if real else WEAK
    for name in names:
        print("%-22s %s" % (name, run(trial, name, image)), flush=True)


if __name__ == "__main__":
    main()
