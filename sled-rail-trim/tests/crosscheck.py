"""The second opinion.

Plain script, no pytest, no plugins, no conftest. It rebuilds the runner from
scratch, draws its own seed, and grades both halves again against the same
sealed part. A run that talked pytest into reporting green still has to get
past this, and the two have to agree.

Exit 0 means it agrees. Anything else means it does not.
"""

import os
import pwd
import secrets
import subprocess
import sys
import tempfile

sys.path.insert(0, "/tests")

import cases
import fingerprints
import harness
import plan
import sessions

RAILS = 20
BATCHES = 10
RUNS = 6


def build_runner(app_dir, workdir, user):
    """Compile the apply path again, from the agent's file and nothing else."""
    binary = os.path.join(workdir, "runner")
    argv = ["cc", "-std=c11", "-O2", "-o", binary,
            "/probe/runner.c", os.path.join(app_dir, "src", "driver.c"),
            "-I", "/probe/include"]
    if user:
        argv = ["setpriv", "--reuid", user, "--regid", user, "--init-groups",
                "--inh-caps", "-all", "--"] + argv
    done = subprocess.run(argv, capture_output=True, text=True)
    if done.returncode != 0:
        print(f"[crosscheck] the apply path did not build: {done.stderr[:400]}",
              file=sys.stderr)
        return ""
    return binary


def main() -> int:
    app_dir = os.environ.get("CHECK_APP", "/app")
    pristine = os.environ.get("CHECK_PRISTINE", "/tests/pristine")
    user = os.environ.get("CHECK_USER", "")

    problems = fingerprints.check(app_dir, pristine)
    if problems:
        print("[crosscheck] fingerprints do not match:", "; ".join(problems),
              file=sys.stderr)
        return 1

    workdir = tempfile.mkdtemp(prefix="crosscheck.")
    os.chmod(workdir, 0o755)
    # The compiler runs as the unprivileged account and has to be able to
    # create the binary here.
    if user:
        try:
            entry = pwd.getpwnam(user)
            os.chown(workdir, entry.pw_uid, entry.pw_gid)
        except (KeyError, PermissionError, OSError):
            os.chmod(workdir, 0o777)
    binary = build_runner(app_dir, workdir, user)
    if not binary:
        return 1

    seed = int(os.environ["CHECK_SEED"]) ^ 0x5EED ^ secrets.randbelow(1 << 20)

    for case in cases.named_cases() + cases.generated_cases(seed, count=8):
        cost = plan.reference_cost(case["rails"], case["start"], case["session"])
        spent, fault, ok, note = harness.drive(
            binary, case["rails"], case["start"], case["session"], cost, user)
        if fault or note or ok != len(case["session"]):
            print(f"[crosscheck] {case['id']} disagrees: "
                  f"{fault or note or 'wrong end state'}", file=sys.stderr)
            return 1

    harness.assert_agent_code_absent(sys.modules, app_dir)

    spent_total = reference_total = 0
    for n in range(RUNS):
        start, session = sessions.build(seed + n * 104729, RAILS, BATCHES)
        cost = plan.reference_cost(RAILS, start, session)
        spent, fault, ok, note = harness.drive(
            binary, RAILS, start, session, cost, user)
        if fault or note or ok != len(session):
            print(f"[crosscheck] the long run disagrees: "
                  f"{fault or note or 'wrong end state'}", file=sys.stderr)
            return 1
        spent_total += spent
        reference_total += cost

    ceiling = plan.ceiling_from(reference_total)
    if spent_total > ceiling:
        print(f"[crosscheck] {spent_total} transactions against a ceiling of "
              f"{ceiling}", file=sys.stderr)
        return 1

    print(f"[crosscheck] every case agrees, and {spent_total} transactions "
          f"against a ceiling of {ceiling}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
