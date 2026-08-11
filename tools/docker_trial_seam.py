#!/usr/bin/env python3
"""Two-container trial emulation for the turn-seam-alignment task.

Reproduces what the platform does, with docker directly, because `harbor` is not
available here: build both images, run the agent script inside the agent image, pull the
declared artifacts out, upload them into the verifier image at their original absolute
paths, run tests/test.sh, and read /logs/verifier/reward.txt.

This is the run that actually exercises the verifier's isolation: the privilege drop, the
locked reward channel, the root-only ground truth. The host emulation in
tools/run_local_seam.py does not.

Usage:
    python3 tools/docker_trial_seam.py --build
    python3 tools/docker_trial_seam.py oracle
    python3 tools/docker_trial_seam.py nop
    python3 tools/docker_trial_seam.py --all
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TASK = ROOT / "tasks" / "turn-seam-alignment"
ENV_IMG = "tsa-env:local"
TEST_IMG = "tsa-test:local"
ARTIFACTS = ["tok/inc.py", "tok/store.py", "loop/ep.py", "loop/rec.py"]


def sh(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


CA = Path("/root/.ccr/ca-bundle.crt")


def local_context(ctx: Path, tmp: Path) -> Path:
    """Copy a build context, adding this sandbox's proxy CA if there is one.

    Local accommodation only. The shipped Dockerfiles are used verbatim; this adds the
    trust the sandbox's TLS-terminating egress proxy needs so pip can resolve at build
    time. On the platform the build has ordinary network access and needs none of it.
    """
    dst = tmp / ctx.name
    shutil.copytree(ctx, dst)
    if not CA.is_file():
        return dst
    shutil.copyfile(CA, dst / "__ca.crt")
    df = dst / "Dockerfile"
    lines = df.read_text().splitlines()
    for i, line in enumerate(lines):
        if line.upper().startswith("FROM "):
            lines[i + 1:i + 1] = [
                "COPY __ca.crt /usr/local/share/ca-certificates/proxy.crt",
                "RUN cat /usr/local/share/ca-certificates/proxy.crt "
                ">> /etc/ssl/certs/ca-certificates.crt",
                "ENV PIP_CERT=/etc/ssl/certs/ca-certificates.crt",
                "ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt",
            ]
            break
    df.write_text("\n".join(lines) + "\n")
    return dst


def build() -> int:
    tmp = Path(tempfile.mkdtemp())
    try:
        for tag, ctx in ((ENV_IMG, TASK / "environment"), (TEST_IMG, TASK / "tests")):
            print("building", tag)
            proc = sh(["docker", "build", "-q", "-t", tag, str(local_context(ctx, tmp))])
            if proc.returncode != 0:
                print(proc.stdout[-3000:], proc.stderr[-3000:])
                return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


def agent_run(script: Path | None, outdir: Path) -> None:
    outdir.mkdir(parents=True, exist_ok=True)
    inner = "true"
    mounts = []
    if script is not None:
        mounts = ["-v", "%s:/agent.sh:ro" % script.resolve()]
        inner = "bash /agent.sh >/tmp/agent.log 2>&1 || true"
    collect = " ; ".join(
        "if [ -f /app/%s ]; then mkdir -p /out/$(dirname %s); cp /app/%s /out/%s; fi"
        % (a, a, a, a) for a in ARTIFACTS)
    proc = sh(["docker", "run", "--rm", "-v", "%s:/out" % outdir.resolve()] + mounts
              + [ENV_IMG, "bash", "-c", "%s ; %s" % (inner, collect)])
    if proc.returncode != 0:
        print("    agent container exited", proc.returncode, proc.stderr[-400:])


def verifier_run(artdir: Path) -> int:
    cmd = (
        "mkdir -p /app/model /app/runtime /app/mem ; "
        "cp -a /artifacts/. /app/ 2>/dev/null ; "
        "mkdir -p /logs/verifier ; "
        "bash /tests/test.sh > /tmp/v.log 2>&1 ; "
        "echo REWARD=$(cat /logs/verifier/reward.txt 2>/dev/null) ; "
        "tail -5 /tmp/v.log"
    )
    proc = sh(["docker", "run", "--rm", "-v", "%s:/artifacts:ro" % artdir.resolve(),
               TEST_IMG, "bash", "-c", cmd])
    reward = 0
    for line in proc.stdout.splitlines():
        if line.startswith("REWARD="):
            try:
                reward = int(line.split("=", 1)[1].strip() or 0)
            except ValueError:
                reward = 0
    tail = [ln for ln in proc.stdout.splitlines() if "passed" in ln or "failed" in ln]
    if tail:
        print("    " + tail[-1].strip())
    return reward


def trial(name: str, script: Path | None, want: int) -> bool:
    print("[%s]" % name)
    tmp = Path(tempfile.mkdtemp())
    try:
        agent_run(script, tmp / "art")
        reward = verifier_run(tmp / "art")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    ok = reward == want
    print("    reward=%d expected=%d -> %s\n" % (reward, want, "PASS" if ok else "FAIL"))
    return ok


def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print(__doc__)
        return 2
    if argv[1] == "--build":
        return build()
    if build() != 0:
        return 1
    if argv[1] == "oracle":
        return 0 if trial("oracle", TASK / "solution" / "solve.sh", 1) else 1
    if argv[1] == "nop":
        return 0 if trial("nop", None, 0) else 1
    if argv[1] == "--all":
        res = [trial("oracle", TASK / "solution" / "solve.sh", 1), trial("nop", None, 0)]
        for cheat in sorted((TASK / "cheat").glob("*.sh")):
            res.append(trial("cheat: " + cheat.name, cheat, 0))
        print("%d/%d trials behaved as required" % (sum(res), len(res)))
        return 0 if all(res) else 1
    return 0 if trial(argv[1], Path(argv[1]), 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
