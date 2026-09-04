"""Which test catches each cheat, and whether it is the one that should.

A sweep that only reads the reward cannot tell a probe that was rejected from
a probe that never ran, so this records the test that named each failure and
holds the integrity probes to their own layer: the one aimed at the executed
tree has to be caught by that check and by nothing else, or the check is doing
nothing and the next session deletes the probe as noise.

Self-contained: it builds the two images out of this bundle and drives docker
itself.

    python3 authoring/cheat_report.py
"""
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

TASK = pathlib.Path(__file__).resolve().parent.parent
SLUG = TASK.name
ENV_IMG = "%s-env:report" % SLUG
TEST_IMG = "%s-test:report" % SLUG
ARTIFACTS = ["note/board.py", "note/rule.py"]
CA_VARS = ("NCF_CA_BUNDLE", "REQUESTS_CA_BUNDLE", "PIP_CERT", "SSL_CERT_FILE")

BOARD_TESTS = {"test_the_fixed_streams_match_the_rule",
               "test_the_generated_streams_match_the_rule",
               "test_the_wide_streams_match_the_rule",
               "test_no_stream_faulted",
               "test_the_board_ran_at_all"}
TREE_TEST = "test_the_executed_tree_was_the_one_we_shipped"
RAN_TEST = "test_the_board_ran_at_all"

# name -> (tests that must fire, tests that must not)
#
# The frozen-tree probe has to be caught by the tree check and by nothing that
# reads the determination, or that check is doing nothing.
#
# The per-thread board is the reference with the settling given up and nothing
# else, so every answer it gives is right and only its cost is wrong: it has to
# be caught by the run being killed before it reports, never by a rule. Check
# it the other way round as well - with the wide block switched off it scores 1
# on every test, which is what says the gate grades cost and not correctness.
EXPECT = {"cheat-probe-rewrite-frozen.sh": ({TREE_TEST}, BOARD_TESTS),
          "cheat-rule-groups-per-thread.sh": ({RAN_TEST}, {TREE_TEST})}


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def ca_bundle():
    """A certificate to trust during the build, or None where the host needs none.

    Which file that is belongs to the host and not to this bundle, so set
    NCF_CA_BUNDLE on a sandbox that terminates TLS.
    """
    for name in CA_VARS:
        got = os.environ.get(name)
        if got and pathlib.Path(got).is_file():
            return pathlib.Path(got)
    return None


def context(src, tmp):
    """Copy a build context, adding this sandbox's proxy CA if there is one.

    Local accommodation only: the shipped Dockerfiles are used verbatim on the
    platform, which needs none of this.
    """
    dst = tmp / src.name
    shutil.copytree(src, dst)
    ca = ca_bundle()
    if ca is None:
        return dst
    shutil.copyfile(ca, dst / "__ca.crt")
    df = dst / "Dockerfile"
    lines = df.read_text().splitlines()
    for i, line in enumerate(lines):
        if line.upper().startswith("FROM "):
            lines[i + 1:i + 1] = [
                "COPY __ca.crt /usr/local/share/ca-certificates/proxy.crt",
                "ENV PIP_CERT=/usr/local/share/ca-certificates/proxy.crt",
                "ENV REQUESTS_CA_BUNDLE=/usr/local/share/ca-certificates/proxy.crt",
            ]
            break
    df.write_text("\n".join(lines) + "\n")
    return dst


def build():
    tmp = pathlib.Path(tempfile.mkdtemp())
    try:
        for src, tag in ((TASK / "environment", ENV_IMG), (TASK / "tests", TEST_IMG)):
            ctx = context(src, tmp)
            got = sh(["docker", "build", "-q", "-t", tag, str(ctx)])
            if got.returncode != 0:
                print(got.stderr[-1500:])
                return False
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return True


def run_one(script):
    out = pathlib.Path(tempfile.mkdtemp())
    try:
        collect = " ; ".join(
            "if [ -f /app/%s ]; then mkdir -p /out/$(dirname %s); cp /app/%s /out/%s; fi"
            % (a, a, a, a) for a in ARTIFACTS)
        sh(["docker", "run", "--rm", "-v", "%s:/out" % out,
            "-v", "%s:/agent.sh:ro" % script.resolve(), ENV_IMG, "bash", "-c",
            "bash /agent.sh >/tmp/a.log 2>&1 || true ; %s" % collect])
        parents = sorted({("/app/" + a).rsplit("/", 1)[0] for a in ARTIFACTS})
        cmd = ("mkdir -p %s ; cp -a /artifacts/. /app/ 2>/dev/null ; "
               "bash /tests/test.sh > /tmp/v.log 2>&1 ; "
               "echo REWARD=$(cat /logs/verifier/reward.txt 2>/dev/null) ; cat /tmp/v.log"
               ) % " ".join(parents)
        got = sh(["docker", "run", "--rm", "-v", "%s:/artifacts:ro" % out,
                  TEST_IMG, "bash", "-c", cmd])
        reward = 0
        for line in got.stdout.splitlines():
            if line.startswith("REWARD="):
                reward = int(line.split("=", 1)[1].strip() or 0)
        return reward, set(re.findall(r"FAILED [^:]*::(\w+)", got.stdout))
    finally:
        shutil.rmtree(out, ignore_errors=True)


def main():
    if shutil.which("docker") is None:
        print("docker is not available; cannot grade the cheats here")
        return 1
    if not build():
        print("build failed")
        return 1
    bad = []
    scripts = sorted((TASK / "cheat").glob("cheat-*.sh"))
    for script in scripts:
        reward, hits = run_one(script)
        must, must_not = EXPECT.get(script.name, (None, set()))
        note = ""
        if reward != 0:
            bad.append("%s scored %d" % (script.name, reward))
            note = "  <- SCORED 1"
        elif not hits:
            bad.append("%s scored 0 but no test named it" % script.name)
            note = "  <- caught by nothing nameable"
        elif must is not None and not (must & hits):
            bad.append("%s missed by %s" % (script.name, ", ".join(sorted(must))))
            note = "  <- wrong layer"
        elif must is not None and (must_not & hits):
            bad.append("%s also caught by %s"
                       % (script.name, ", ".join(sorted(must_not & hits))))
            note = "  <- caught by more than its own layer"
        print("  %-38s reward=%d  %s%s" % (script.name, reward, ",".join(sorted(hits)), note))
    if bad:
        print("FAIL %d cheat(s) misbehaved: %s" % (len(bad), "; ".join(bad)))
        return 1
    print("all %d cheats score 0 and each is caught by the layer it is aimed at"
          % len(scripts))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
