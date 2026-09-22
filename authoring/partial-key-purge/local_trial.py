"""tools/docker_trial.py with one local accommodation for this sandbox. Authoring only.

The session's egress policy answers 403 to deb.debian.org (recorded in STATE.md), so the test
image's `apt-get install procps util-linux` cannot run here. The base image already carries
util-linux (setpriv, setsid) and coreutils (timeout), and procps is not used by test.sh, so the
local build drops only the apt half of that RUN line and keeps the pinned pip install, which
reaches PyPI directly. Everything else - the shipped Dockerfiles, the agent run, the artifact
hand-off, test.sh inside the verifier image - is docker_trial.py unchanged. On the platform the
shipped Dockerfile builds as written.

    python local_trial.py oracle | nop | --dir <path> | --cheat <script> | --all
    python local_trial.py --cpus 1 --memory 2g oracle     (resource caps on the verifier run)
"""
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "tools"))
import docker_trial  # noqa: E402

CAPS = []


def local_test_context(ctx, tmp):
    dst = docker_trial.local_context(ctx, tmp)
    df = dst / "Dockerfile"
    text = df.read_text()
    new, n = re.subn(
        r"RUN apt-get update \\\n\s+&& apt-get install -y --no-install-recommends util-linux procps \\\n"
        r"\s+&& rm -rf /var/lib/apt/lists/\*\n", "", text)
    assert n == 1, "the apt line in tests/Dockerfile changed; update local_trial.py"
    df.write_text(new)
    return dst


class Local(docker_trial.Trial):
    def build(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            for tag, ctx, fix in ((self.env_img, self.task / "environment", docker_trial.local_context),
                                  (self.test_img, self.task / "tests", local_test_context)):
                print("building", tag)
                proc = docker_trial.sh(["docker", "build", "-q", "--network", "host", "-t", tag,
                                        str(fix(ctx, tmp))])
                if proc.returncode != 0:
                    print(proc.stdout[-3000:], proc.stderr[-3000:])
                    return 1
        finally:
            shutil.rmtree(tmp, ignore_errors=True)
        return 0

    def verifier_run(self, artdir):
        if not CAPS:
            return super().verifier_run(artdir)
        real = docker_trial.sh

        def capped(cmd, **kw):
            if cmd[:3] == ["docker", "run", "--rm"]:
                cmd = cmd[:3] + CAPS + cmd[3:]
            return real(cmd, **kw)

        docker_trial.sh = capped
        try:
            return super().verifier_run(artdir)
        finally:
            docker_trial.sh = real


def main(argv):
    while argv[1:2] and argv[1] in ("--cpus", "--memory"):
        CAPS.extend([argv[1], argv[2]])
        del argv[1:3]
    t = Local("partial-key-purge")
    what = argv[1]
    if t.build() != 0:
        return 1
    if what == "oracle":
        return 0 if t.run("oracle", t.task / "solution" / "solve.sh", 1, bundle=True) else 1
    if what == "nop":
        return 0 if t.run("nop", None, 0) else 1
    if what == "--dir":
        d = Path(argv[2]).resolve()
        return 0 if t.run("variant: " + d.name, t.from_dir(d), 1) else 1
    if what == "--cheat":
        p = Path(argv[2]).resolve()
        return 0 if t.run("cheat: " + p.name, p, 0) else 1
    if what == "--all":
        res = [t.run("oracle", t.task / "solution" / "solve.sh", 1, bundle=True), t.run("nop", None, 0)]
        for cheat in sorted((t.task / "cheat").glob("*.sh")):
            res.append(t.run("cheat: " + cheat.name, cheat, 0))
        print("%d/%d trials behaved as required" % (sum(res), len(res)))
        return 0 if all(res) else 1
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv))
