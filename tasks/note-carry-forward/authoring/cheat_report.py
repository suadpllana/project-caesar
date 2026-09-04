"""Which test catches each cheat, and whether it is the one that should.

A sweep that only reads the reward cannot tell a probe that was rejected from
a probe that never ran. Every cheat here has to be caught, and the probes aimed
at an attestation have to be caught by that attestation and by nothing else --
otherwise the layer they exist to exercise is untested and the next session
deletes them as noise.
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import docker_trial2 as dt  # noqa: E402

SLUG = "note-carry-forward"
BOARD_TESTS = {"test_the_fixed_streams_match_the_rule",
               "test_the_generated_streams_match_the_rule",
               "test_no_stream_faulted",
               "test_the_board_ran_at_all"}
TREE_TEST = "test_the_executed_tree_was_the_one_we_shipped"

# name -> the tests that must fire, and the tests that must NOT
EXPECT = {
    "cheat-probe-rewrite-frozen.sh": ({TREE_TEST}, BOARD_TESTS),
}


def failed_tests(trial, script, bundle=False):
    tmp = pathlib.Path(tempfile.mkdtemp())
    try:
        trial.agent_run(script, tmp / "art", bundle)
        artdir = tmp / "art"
        parents = sorted({str(pathlib.Path("/app") / a).rsplit("/", 1)[0] for a in trial.arts})
        cmd = ("mkdir -p %s ; cp -a /artifacts/. /app/ 2>/dev/null ; "
               "mkdir -p /logs/verifier ; bash /tests/test.sh > /tmp/v.log 2>&1 ; "
               "echo REWARD=$(cat /logs/verifier/reward.txt 2>/dev/null) ; cat /tmp/v.log"
               ) % " ".join(parents)
        proc = dt.sh(["docker", "run", "--rm", "-v", "%s:/artifacts:ro" % artdir.resolve(),
                      trial.test_img, "bash", "-c", cmd])
        reward = 0
        for line in proc.stdout.splitlines():
            if line.startswith("REWARD="):
                reward = int(line.split("=", 1)[1].strip() or 0)
        hits = set(re.findall(r"FAILED [^:]*::(\w+)", proc.stdout))
        return reward, hits
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def main():
    trial = dt.Trial(SLUG)
    if trial.build() != 0:
        print("build failed")
        return 1
    task = ROOT / "tasks" / SLUG
    bad = []
    for script in sorted((task / "cheat").glob("cheat-*.sh")):
        reward, hits = failed_tests(trial, script)
        must, must_not = EXPECT.get(script.name, (None, set()))
        note = ""
        if reward != 0:
            bad.append("%s scored %d" % (script.name, reward))
            note = "  <- SCORED 1"
        elif not hits:
            bad.append("%s scored 0 but no test named it" % script.name)
            note = "  <- caught by nothing nameable"
        elif must is not None and not (must & hits):
            bad.append("%s not caught by %s" % (script.name, ", ".join(sorted(must))))
            note = "  <- wrong layer"
        elif must is not None and (must_not & hits):
            bad.append("%s also caught by %s" % (script.name, ", ".join(sorted(must_not & hits))))
            note = "  <- caught by more than its own layer"
        print("  %-38s reward=%d  %s%s" % (script.name, reward, ",".join(sorted(hits)), note))
    if bad:
        print("FAIL %d cheat(s) misbehaved: %s" % (len(bad), "; ".join(bad)))
        return 1
    print("all %d cheats score 0 and each is caught by the layer it is aimed at"
          % len(list((task / "cheat").glob("cheat-*.sh"))))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
