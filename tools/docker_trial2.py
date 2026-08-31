#!/usr/bin/env python3
"""Two-container trial emulation, for any task in tasks/.

Reproduces what the platform does, with docker directly, because `harbor` is not available
here: build both images, run the agent script inside the agent image, pull the declared
artifacts out, upload them into the verifier image at their original absolute paths, run
tests/test.sh, and read /logs/verifier/reward.txt.

This is the run that actually exercises the verifier's isolation: the privilege drop, the
locked reward channel, the root-only ground truth. The host emulation in the task's own
authoring/ scripts does not.

Usage:
    python3 tools/docker_trial2.py <slug> --build
    python3 tools/docker_trial2.py <slug> oracle
    python3 tools/docker_trial2.py <slug> nop
    python3 tools/docker_trial2.py <slug> --all
    python3 tools/docker_trial2.py <slug> --dir authoring/variants/ok-flat
"""

from __future__ import annotations

import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CA = Path("/root/.ccr/ca-bundle.crt")


def sh(cmd: list[str], **kw) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def artifacts(task: Path) -> list[str]:
    text = (task / "task.toml").read_text()
    block = text.split("artifacts", 1)[1].split("]", 1)[0]
    return [m.group(1).lstrip("/").replace("app/", "", 1)
            for m in re.finditer(r'"([^"]+)"', block)]


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


class Trial:
    def __init__(self, slug: str):
        self.task = ROOT / "tasks" / slug
        self.env_img = "%s-env:local" % slug
        self.test_img = "%s-test:local" % slug
        self.arts = artifacts(self.task)

    def build(self) -> int:
        tmp = Path(tempfile.mkdtemp())
        try:
            for tag, ctx in ((self.env_img, self.task / "environment"),
                             (self.test_img, self.task / "tests")):
                print("building", tag)
                proc = sh(["docker", "build", "-q", "-t", tag, str(local_context(ctx, tmp))])
                if proc.returncode != 0:
                    print(proc.stdout[-3000:], proc.stderr[-3000:])
                    return 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return 0

    def agent_run(self, script: Path | None, outdir: Path, bundle: bool = False) -> None:
        outdir.mkdir(parents=True, exist_ok=True)
        inner = "true"
        mounts: list[str] = []
        if script is not None and bundle:
            # The platform hands the oracle agent the whole solution/ directory, so a
            # solve.sh may read files that sit beside it - which is how a reference
            # longer than a few lines avoids being inlined as a heredoc and duplicated.
            # Mounting only the script cannot run such a solution and silently scores 0.
            mounts = ["-v", "%s:/solution:ro" % script.parent.resolve()]
            inner = "bash /solution/%s >/tmp/agent.log 2>&1 || true" % script.name
        elif script is not None:
            mounts = ["-v", "%s:/agent.sh:ro" % script.resolve()]
            inner = "bash /agent.sh >/tmp/agent.log 2>&1 || true"
        collect = " ; ".join(
            "if [ -f /app/%s ]; then mkdir -p /out/$(dirname %s); cp /app/%s /out/%s; fi"
            % (a, a, a, a) for a in self.arts)
        proc = sh(["docker", "run", "--rm", "-v", "%s:/out" % outdir.resolve()] + mounts
                  + [self.env_img, "bash", "-c", "%s ; %s" % (inner, collect)])
        if proc.returncode != 0:
            print("    agent container exited", proc.returncode, proc.stderr[-400:])

    def verifier_run(self, artdir: Path) -> int:
        parents = sorted({str(Path("/app") / a).rsplit("/", 1)[0] for a in self.arts})
        cmd = (
            "mkdir -p %s ; "
            "cp -a /artifacts/. /app/ 2>/dev/null ; "
            "mkdir -p /logs/verifier ; "
            "bash /tests/test.sh > /tmp/v.log 2>&1 ; "
            "echo REWARD=$(cat /logs/verifier/reward.txt 2>/dev/null) ; "
            "tail -5 /tmp/v.log"
        ) % " ".join(parents)
        proc = sh(["docker", "run", "--rm", "-v", "%s:/artifacts:ro" % artdir.resolve(),
                   self.test_img, "bash", "-c", cmd])
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

    def run(self, name: str, script: Path | None, want: int,
            bundle: bool = False) -> bool:
        print("[%s]" % name)
        tmp = Path(tempfile.mkdtemp())
        try:
            self.agent_run(script, tmp / "art", bundle)
            reward = self.verifier_run(tmp / "art")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        ok = reward == want
        print("    reward=%d expected=%d -> %s\n" % (reward, want, "PASS" if ok else "FAIL"))
        return ok

    def from_dir(self, d: Path) -> Path:
        """Turn a directory of editable files into an agent script, for variant checks."""
        by_base = {Path(a).name: a for a in self.arts}
        lines = ["#!/bin/bash", "set -euo pipefail", ""]
        for f in sorted(d.glob("*.py")):
            rel = by_base.get(f.name)
            if rel is None:
                continue
            lines += ["cat > /app/%s <<'PYEOF'" % rel, f.read_text().rstrip("\n"), "PYEOF", ""]
        out = Path(tempfile.mkdtemp()) / "variant.sh"
        out.write_text("\n".join(lines) + "\n")
        return out


def main(argv: list[str]) -> int:
    if len(argv) < 3:
        print(__doc__)
        return 2
    t = Trial(argv[1])
    what = argv[2]
    if what == "--build":
        return t.build()
    if t.build() != 0:
        return 1
    if what == "oracle":
        return 0 if t.run("oracle", t.task / "solution" / "solve.sh", 1, bundle=True) else 1
    if what == "nop":
        return 0 if t.run("nop", None, 0) else 1
    if what == "--dir":
        d = Path(argv[3])
        if not d.is_absolute():
            d = t.task / d
        return 0 if t.run("variant: " + d.name, t.from_dir(d), 1) else 1
    if what == "--variants":
        res = []
        for d in sorted((t.task / "authoring" / "variants").iterdir()):
            if d.is_dir() and d.name.startswith("ok-"):
                res.append(t.run("variant: " + d.name, t.from_dir(d), 1))
        print("%d/%d variants scored 1" % (sum(res), len(res)))
        return 0 if all(res) else 1
    if what == "--all":
        res = [t.run("oracle", t.task / "solution" / "solve.sh", 1, bundle=True), t.run("nop", None, 0)]
        for cheat in sorted((t.task / "cheat").glob("*.sh")):
            res.append(t.run("cheat: " + cheat.name, cheat, 0))
        print("%d/%d trials behaved as required" % (sum(res), len(res)))
        return 0 if all(res) else 1
    return 0 if t.run(what, Path(what), 0) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv))
