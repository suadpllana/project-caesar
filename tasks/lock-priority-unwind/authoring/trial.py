#!/usr/bin/env python3
"""Host emulation of the verifier: real runner, real pytest, real gt.json.

Docker is not installed on the authoring host, so tools/docker_trial2.py cannot run here. This
reproduces everything the verifier does EXCEPT the container isolation: it lays a policy over an
untouched copy of the tree, runs tests/runner.py against it, and grades the result with the real
tests/test_outputs.py, drawn scenarios and all.

What it therefore does NOT prove: the privilege drop, the locked reward channel, the root-only
model and ground truth, and the sweep of double-forked survivors. Those need the two real images
and are listed as unrun in the handover.

Usage:
    python3 authoring/trial.py solution
    python3 authoring/trial.py --all
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

TASK = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "authoring"))

import harness  # noqa: E402


class HarnessFault(RuntimeError):
    """The grader did not run. Distinct from the grader running and rejecting."""


def preflight() -> None:
    """Refuse to grade anything until the grader itself can start.

    A reward of 0 means "the verifier ran and rejected this submission". When pytest is
    missing, `python -m pytest` also exits non-zero, and every target in the sweep comes back
    0 - reference, variants and cheats alike - which reads as a clean cheat sweep and is in
    fact a harness that never graded anything. CLAUDE.md records that failure twice already;
    this is the check that stops it happening a third time.

    Only pytest is required here. The container verifier also needs pytest-json-ctrf, because
    `tests/test.sh` passes `--ctrf`; this host emulation does not, and demanding it would fail
    a run that is perfectly able to grade.
    """
    probe = subprocess.run([sys.executable, "-m", "pytest", "--version"],
                           capture_output=True, text=True)
    if probe.returncode != 0:
        raise HarnessFault(
            "cannot grade: `%s -m pytest` does not run, so every target would come back 0.\n"
            "    pip install pytest==9.1.1\n%s"
            % (sys.executable, (probe.stderr or probe.stdout)[-500:]))


def grade(variant: str) -> tuple[int, str]:
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        app = tmp / "app"
        harness.overlay(variant, app)
        out = tmp / "out.json"
        nonce = "hostrun"
        subprocess.run([sys.executable, str(TASK / "tests" / "runner.py"), str(out)],
                       capture_output=True, text=True,
                       env=harness.env_for(app, {"RUN_NONCE": nonce, "TMPDIR": str(tmp)}),
                       timeout=900)
        if not out.is_file():
            out.write_text(json.dumps({"runs": {}, "broke": {"fatal": "no output"}}))
        art = tmp / "artifact"
        harness.stage(variant, art)
        proc = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", str(TASK / "tests" / "test_outputs.py")],
            capture_output=True, text=True,
            env={"RUN_OUT": str(out), "RUN_NONCE": nonce, "APP_DIR": str(app),
                 "PRISTINE_DIR": str(TASK / "environment" / "app_src"),
                 "ARTIFACT_DIR": str(art), "PYTHONPATH": str(TASK / "tests"),
                 "PYTHONDONTWRITEBYTECODE": "1", "SYSTEMROOT": "C:/Windows",
                 "PATH": "/usr/bin:/bin"},
            timeout=900)
        # 0 = every assertion held, 1 = the grader ran and rejected. Anything else is the
        # grader failing to start or dying, which is not a verdict about the submission.
        if proc.returncode not in (0, 1):
            raise HarnessFault("pytest exited %d, so nothing was graded:\n%s\n%s"
                               % (proc.returncode, proc.stdout[-2000:], proc.stderr[-2000:]))
        if "passed" not in proc.stdout and "failed" not in proc.stdout:
            raise HarnessFault("pytest collected no tests, so nothing was graded:\n%s\n%s"
                               % (proc.stdout[-2000:], proc.stderr[-2000:]))
        return (1 if proc.returncode == 0 else 0), proc.stdout[-2500:]


def targets() -> list[tuple[str, str]]:
    out = [("oracle", "solution"), ("nop", "shipped")]
    for d in sorted((TASK / "authoring" / "variants").glob("ok-*")):
        out.append((d.name, "authoring/variants/" + d.name))
    for f in sorted((TASK / "cheat").glob("cheat-*.sh")):
        out.append((f.stem[len("cheat-"):], "cheat/" + f.name))
    return out


def main(argv: list[str]) -> int:
    if len(argv) < 2:
        print(__doc__)
        return 2
    preflight()
    if argv[1] == "--all":
        bad = 0
        for label, path in targets():
            r, _ = grade(path)
            want = 1 if (label == "oracle" or label.startswith("ok-")) else 0
            if r != want:
                bad += 1
            print("%s %-30s reward=%d (want %d)"
                  % ("OK " if r == want else "BAD", label, r, want))
        print("\n%d unexpected" % bad)
        return 1 if bad else 0
    r, tail = grade(argv[1])
    print(tail)
    print("reward=%d" % r)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
