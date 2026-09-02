#!/usr/bin/env python3
"""Two-image trial for earliest-change-script, which is not in the kit layout.

tools/docker_trial2.py reads an artifact list out of task.toml and overlays an
app tree; this bundle has no app tree at all - the agent writes one file from
scratch - so it needs its own runner. The real tests/Dockerfile and the real
tests/test.sh are used unchanged; only the build context is doctored, and only
in the two ways the authoring sandbox forces:

  * the egress CA bundle is injected so pip can reach the index, and
  * the apt layer is dropped, because deb.debian.org answers 403 through the
    proxy here.

Dropping apt costs pkill, so the teardown between the sandbox account and the
grading account is NOT exercised locally. Say so in any handover. Everything
else is the shipped verifier: the privilege drop, the root-owned reward
channel, the unreadable /tests, the per-case budgets and the real grader.

  python3 tools/ecs_trial.py --all
  python3 tools/ecs_trial.py --oracle --repeat 3
  python3 tools/ecs_trial.py --variants
  python3 tools/ecs_trial.py --margins

--all runs the oracle, the nop, every cheat/*.py expecting 0, and every
authoring/variants/*/change_script.py expecting 1: an alternative correct
implementation that scores 0 means a budget or a comparison is grading an
implementation choice, which is the run-audit rejection.
"""

import argparse
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
TASK = ROOT / "tasks" / "earliest-change-script"
CA = pathlib.Path("/root/.ccr/ca-bundle.crt")
TESTS_IMAGE = "ecs-trial-tests"
LIMITS = ["--cpus=2", "--memory=4096m"]

APT = re.compile(r"RUN apt-get update.*?rm -rf /var/lib/apt/lists/\*\n",
                 re.DOTALL)


def build_tests_image():
    with tempfile.TemporaryDirectory() as tmp:
        ctx = pathlib.Path(tmp) / "tests"
        shutil.copytree(TASK / "tests", ctx)
        text = (ctx / "Dockerfile").read_text()
        text = APT.sub("# apt layer dropped for the local trial\n", text)
        if CA.exists():
            shutil.copy(CA, ctx / "ca-bundle.crt")
            lines = text.split("\n")
            for i, line in enumerate(lines):
                if line.startswith("FROM "):
                    lines[i + 1:i + 1] = [
                        "COPY ca-bundle.crt /usr/local/share/ca-certificates/ccr.crt",
                        "ENV PIP_CERT=/usr/local/share/ca-certificates/ccr.crt",
                        "ENV SSL_CERT_FILE=/usr/local/share/ca-certificates/ccr.crt",
                    ]
                    break
            text = "\n".join(lines)
        (ctx / "Dockerfile").write_text(text)
        done = subprocess.run(["docker", "build", "-q", "-t", TESTS_IMAGE,
                               str(ctx)], capture_output=True, text=True)
        if done.returncode:
            sys.exit("tests image build failed:\n" + done.stderr[-2000:])


HEADROOM = 1.5

# The sandbox this runs on is not the machine that grades. The 2026-08-31
# rejection reproduced exactly in a sandbox where the pairs engine took 5.41 s
# on timed case 13; the sandbox of 2026-09-02 ran the identical code on the
# identical case in 2.05 s. Every measurement here is therefore scaled by this
# before it is held to the headroom, and the raw figure is printed beside it.
HOST_FACTOR = 2.7


def margins():
    """What the reference has left over on the machine that grades it.

    The 2026-08-31 reference-verification rejection was a budget with no
    headroom: the reference sat at 90-113% of a 6 s per-case budget on two
    cores, so which pairs it lost changed with the speed of the host. A budget
    is only calibrated if the reference clears it by a margin no plausible
    machine eats, and the machine is assumed HOST_FACTOR slower than here."""
    with tempfile.TemporaryDirectory() as tmp:
        logs = pathlib.Path(tmp) / "logs"
        logs.mkdir()
        subprocess.run(["docker", "run", "--rm"] + LIMITS + [
            "-v", "%s:/logs" % logs,
            "-v", "%s:/app/change_script.py:ro"
            % (TASK / "solution" / "change_script.py"),
            TESTS_IMAGE, "bash", "-c",
            "/tests/test.sh; cp /tmp/results/report.json /logs/report.json"],
            capture_output=True, text=True)
        report = json.loads((logs / "report.json").read_text() or "{}")

    sys.path.insert(0, str(TASK / "tests"))
    import casegen
    rows = [("cases", report.get("cases_seconds"), 900.0),
            ("medium", report.get("medium_seconds"), casegen.MEDIUM_BUDGET)]
    for index, entry in enumerate(report.get("timed") or []):
        rows.append(("timed %d (%s)" % (index, casegen.TIMED_SHAPES[index][0]),
                     entry.get("seconds"), casegen.TIMED_BUDGET))

    worst = None
    for label, secs, budget in rows:
        if not isinstance(secs, (int, float)):
            print("BAD %-26s no timing" % label)
            worst = 0.0
            continue
        scaled = secs * HOST_FACTOR
        room = budget / scaled if scaled else float("inf")
        mark = "ok " if room >= HEADROOM else "BAD"
        print("%s %-26s %7.2f s here, %6.2f s scaled, of %5.1f  %.1fx headroom"
              % (mark, label, secs, scaled, budget, room))
        worst = room if worst is None else min(worst, room)
    print("\nworst headroom %.1fx after scaling by %.1f, wanted %.1fx"
          % (worst or 0.0, HOST_FACTOR, HEADROOM))
    return 0 if (worst or 0.0) >= HEADROOM else 1


def run_one(label, submission):
    """One graded run. `submission` is a path to the module, or None for nop.

    test.sh draws its own RUN_SEED every time, so running the same submission
    twice is two seeds, which is the shape the pipeline grades in."""
    with tempfile.TemporaryDirectory() as tmp:
        logs = pathlib.Path(tmp) / "logs"
        logs.mkdir()
        cmd = ["docker", "run", "--rm"] + LIMITS + [
            "-v", "%s:/logs" % logs]
        if submission is not None:
            cmd += ["-v", "%s:/app/change_script.py:ro" % submission]
        cmd += [TESTS_IMAGE, "bash", "/tests/test.sh"]
        subprocess.run(cmd, capture_output=True, text=True)
        reward_file = logs / "verifier" / "reward.txt"
        reward = reward_file.read_text().strip() if reward_file.exists() else "?"
        out = logs / "verifier" / "test-stdout.txt"
        failed = []
        if out.exists():
            for line in out.read_text().split("\n"):
                if line.startswith("FAILED "):
                    failed.append(line.split("::")[-1].split(" ")[0])
        return reward, failed


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--all", action="store_true")
    ap.add_argument("--oracle", action="store_true")
    ap.add_argument("--nop", action="store_true")
    ap.add_argument("--cheats", action="store_true")
    ap.add_argument("--variants", action="store_true",
                    help="alternative correct implementations, expecting 1")
    ap.add_argument("--repeat", type=int, default=1,
                    help="graded runs per submission; each draws a fresh seed")
    ap.add_argument("--margins", action="store_true",
                    help="what the reference has left over on every budget")
    ap.add_argument("--no-build", action="store_true")
    args = ap.parse_args()
    if args.margins:
        if not args.no_build:
            build_tests_image()
        return margins()
    if not (args.all or args.oracle or args.nop or args.cheats
            or args.variants):
        args.all = True

    if not args.no_build:
        build_tests_image()

    plan = []
    if args.all or args.oracle:
        plan.append(("oracle", TASK / "solution" / "change_script.py", "1"))
    if args.all or args.nop:
        plan.append(("nop", None, "0"))
    if args.all or args.cheats:
        for path in sorted((TASK / "cheat").glob("*.py")):
            plan.append(("cheat/" + path.name, path, "0"))
    if args.all or args.variants:
        for path in sorted((TASK / "authoring" / "variants").glob(
                "*/change_script.py")):
            plan.append(("variant/" + path.parent.name, path, "1"))

    bad = 0
    for label, path, want in plan:
        for attempt in range(args.repeat):
            reward, failed = run_one(label, path)
            mark = "ok " if reward == want else "BAD"
            if reward != want:
                bad += 1
            print("%s %-38s reward=%s want=%s  %s"
                  % (mark, label, reward, want, ",".join(failed) or "-"))
            sys.stdout.flush()
    total = len(plan) * args.repeat
    print("\n%d of %d as expected" % (total - bad, total))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
