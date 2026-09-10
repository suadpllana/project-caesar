"""Run one isolation probe through the two containers and print what it actually saw.

A probe that scores 0 proves nothing on its own: it would score 0 with its attack removed,
because it is built on the shipped modules. The evidence is the note it leaves in
/work/probe.log - the uid it held, the error each sealed path gave it - and the verifier's
own log. This prints both.
"""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(ROOT / "tools"))
import docker_trial as dt  # noqa: E402


def main():
    name = sys.argv[1]
    t = dt.Trial("span-claim-charge")
    cheat = t.task / "cheat" / name
    tmp = pathlib.Path(tempfile.mkdtemp())
    try:
        art = tmp / "art"
        t.agent_run(cheat, art)
        parents = sorted({str(pathlib.Path("/app") / a).rsplit("/", 1)[0] for a in t.arts})
        cmd = (
            "mkdir -p %s ; cp -a /artifacts/. /app/ 2>/dev/null ; mkdir -p /logs/verifier ; "
            "bash /tests/test.sh > /tmp/v.log 2>&1 ; "
            "echo '--- reward ---' ; cat /logs/verifier/reward.txt ; "
            "echo '--- probe log ---' ; cat /work/probe.log 2>/dev/null || echo '(none)' ; "
            "echo '--- verifier log ---' ; head -30 /tmp/v.log"
        ) % " ".join(parents)
        proc = subprocess.run(
            ["docker", "run", "--rm", "-v", "%s:/artifacts:ro" % art.resolve(),
             t.test_img, "bash", "-c", cmd], capture_output=True, text=True)
        print(proc.stdout)
        if proc.stderr.strip():
            print("stderr:", proc.stderr[-500:])
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main()
