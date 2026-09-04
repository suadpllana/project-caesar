"""Self-contained two-image trial for this bundle.

Builds both images from the shipped Dockerfiles, runs an agent script in the
environment image, lifts the declared artifacts out, drops them into the
verifier image at their original absolute paths and runs tests/test.sh. Unlike
a summary-only driver this keeps the whole pytest log, because which assertion
fired is the only thing that says a probe was rejected by the layer it attacked
rather than by an ImportError.

The only local accommodation is a proxy CA, added to a copy of the build context
so pip can resolve where a sandbox terminates TLS. Which file that is belongs to
the host and not to this bundle, so it is read from the environment and skipped
when nothing names one. The shipped Dockerfiles are used verbatim.
"""

import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SLUG = os.path.basename(ROOT)


def ca_bundle():
    """A certificate to trust during the build, or None when the host needs none.

    Set CAESAR_CA_BUNDLE to a proxy root on a sandbox that terminates TLS.
    """
    for name in ("CAESAR_CA_BUNDLE", "REQUESTS_CA_BUNDLE", "PIP_CERT", "SSL_CERT_FILE"):
        got = os.environ.get(name)
        if got and os.path.isfile(got):
            return got
    return None


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def artifacts():
    body = open(os.path.join(ROOT, "task.toml")).read()
    block = body.split("artifacts", 1)[1].split("]", 1)[0]
    return [m.group(1)[len("/app/"):] for m in re.finditer(r'"([^"]+)"', block)]


def context(where, tmp):
    dst = os.path.join(tmp, os.path.basename(where) + "-ctx")
    shutil.copytree(where, dst)
    ca = ca_bundle()
    if ca is None:
        return dst
    shutil.copyfile(ca, os.path.join(dst, "__ca.crt"))
    docker = os.path.join(dst, "Dockerfile")
    lines = open(docker).read().splitlines()
    for i, line in enumerate(lines):
        if line.upper().startswith("FROM "):
            lines[i + 1:i + 1] = [
                "COPY __ca.crt /usr/local/share/ca-certificates/__ca.crt",
                "RUN cat /usr/local/share/ca-certificates/__ca.crt "
                ">> /etc/ssl/certs/ca-certificates.crt",
                "ENV REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt",
                "ENV PIP_CERT=/etc/ssl/certs/ca-certificates.crt",
            ]
            break
    with open(docker, "w", newline="\n") as fh:
        fh.write("\n".join(lines) + "\n")
    return dst


def build():
    tmp = tempfile.mkdtemp(prefix="psr-build-")
    try:
        for tag, where in ((SLUG + "-env:local", os.path.join(ROOT, "environment")),
                           (SLUG + "-test:local", os.path.join(ROOT, "tests"))):
            got = sh(["docker", "build", "-q", "-t", tag, context(where, tmp)])
            if got.returncode != 0:
                print("build failed for %s\n%s" % (tag, got.stderr[-1500:]))
                return False
        return True
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def once(script, bundle=False):
    """Run one agent script and return (reward, full pytest log)."""
    arts = artifacts()
    tmp = tempfile.mkdtemp(prefix="psr-run-")
    try:
        out = os.path.join(tmp, "art")
        os.makedirs(out)
        mounts, inner = [], "true"
        if script and bundle:
            mounts = ["-v", os.path.dirname(os.path.abspath(script)) + ":/solution:ro"]
            inner = "bash /solution/%s >/tmp/a.log 2>&1 || true" % os.path.basename(script)
        elif script:
            mounts = ["-v", os.path.abspath(script) + ":/agent.sh:ro"]
            inner = "bash /agent.sh >/tmp/a.log 2>&1 || true"
        lift = " ; ".join(
            "if [ -f /app/%s ]; then mkdir -p /out/$(dirname %s); cp /app/%s /out/%s; fi"
            % (a, a, a, a) for a in arts)
        sh(["docker", "run", "--rm", "-v", out + ":/out"] + mounts
           + [SLUG + "-env:local", "bash", "-c", inner + " ; " + lift])
        parents = sorted(set("/app/" + a.rsplit("/", 1)[0] for a in arts))
        cmd = ("mkdir -p %s ; cp -a /artifacts/. /app/ 2>/dev/null ; "
               "bash /tests/test.sh > /tmp/v.log 2>&1 ; "
               "echo REWARD=$(cat /logs/verifier/reward.txt 2>/dev/null) ; "
               "cat /tmp/v.log") % " ".join(parents)
        got = sh(["docker", "run", "--rm", "--cpus=2", "--memory=4096m",
                  "-v", out + ":/artifacts:ro", SLUG + "-test:local", "bash", "-c", cmd])
        reward = 0
        for line in got.stdout.splitlines():
            if line.startswith("REWARD="):
                try:
                    reward = int(line.split("=", 1)[1].strip() or 0)
                except ValueError:
                    reward = 0
        return reward, got.stdout
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def failed(log):
    names = set()
    for line in log.splitlines():
        hit = re.match(r"FAILED\s+[^:]*::([A-Za-z0-9_]+)", line.strip())
        if hit:
            names.add(hit.group(1))
    return sorted(names)


if __name__ == "__main__":
    if not build():
        sys.exit(1)
    what = sys.argv[1] if len(sys.argv) > 1 else "oracle"
    if what == "oracle":
        reward, log = once(os.path.join(ROOT, "solution", "solve.sh"), bundle=True)
    elif what == "nop":
        reward, log = once(None)
    else:
        reward, log = once(what)
    print("reward=%d  failed=%s" % (reward, ", ".join(failed(log)) or "(none)"))
