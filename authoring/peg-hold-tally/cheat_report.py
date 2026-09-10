"""Run cheats in the two containers and report which layer stopped each one.

A reward of 0 is not evidence on its own: a probe that fails for its own reasons - a syntax
error, an import that was never reached - scores 0 and proves nothing (CLAUDE.md, 2026-09-06).
This runs each cheat the way the platform does, then reads back the verifier's own log and the
note the probe left in the work directory, so the report names the test that failed and what the
probe was actually able to do.

Usage: python cheat_report.py [name-fragment ...]
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "peg-hold-tally"
ENV_IMG = "peg-hold-tally-env:local"
TEST_IMG = "peg-hold-tally-test:local"

VERIFY = (
    "mkdir -p /app/keep ; cp -a /artifacts/. /app/ 2>/dev/null ; mkdir -p /logs/verifier ; "
    "bash /tests/test.sh > /tmp/v.log 2>&1 ; "
    "echo REWARD=$(cat /logs/verifier/reward.txt 2>/dev/null) ; "
    "echo ---LOG--- ; grep -E '^(FAILED|ERROR|worker exit|reaped)' /tmp/v.log | head -6 ; "
    "echo ---PROBE--- ; cat /work/probe.log 2>/dev/null | head -4"
)


def run(cheat):
    tmp = pathlib.Path(tempfile.mkdtemp())
    art = tmp / "art"
    art.mkdir()
    try:
        subprocess.run(
            ["docker", "run", "--rm", "-v", "%s:/agent.sh:ro" % cheat.resolve(),
             "-v", "%s:/out" % art.resolve(), ENV_IMG, "bash", "-c",
             "bash /agent.sh >/tmp/a.log 2>&1 || true ; mkdir -p /out/keep ; "
             "cp /app/keep/*.py /out/keep/ 2>/dev/null || true"],
            capture_output=True, text=True)
        got = subprocess.run(
            ["docker", "run", "--rm", "-v", "%s:/artifacts:ro" % art.resolve(),
             TEST_IMG, "bash", "-c", VERIFY], capture_output=True, text=True)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    out = got.stdout
    reward = 0
    m = re.search(r"REWARD=(\d+)", out)
    if m:
        reward = int(m.group(1))
    log = out.split("---LOG---", 1)[1].split("---PROBE---")[0].strip() if "---LOG---" in out else ""
    probe = out.split("---PROBE---", 1)[1].strip() if "---PROBE---" in out else ""
    return reward, log, probe


def main(argv):
    want = argv[1:]
    rows = []
    for cheat in sorted((TASK / "cheat").glob("*.sh")):
        if want and not any(w in cheat.name for w in want):
            continue
        reward, log, probe = run(cheat)
        rows.append({"cheat": cheat.name, "reward": reward, "caught_by": log, "probe": probe})
        print("%-34s reward=%d" % (cheat.name, reward), flush=True)
        for line in log.splitlines()[:4]:
            print("      %s" % line.strip()[:150])
        for line in probe.splitlines()[:3]:
            print("      probe: %s" % line.strip()[:150])
    (HERE / "cheat_report.json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    bad = [r["cheat"] for r in rows if r["reward"] != 0]
    print("\n%d cheats, %d scored 1: %s" % (len(rows), len(bad), bad or "none"))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
