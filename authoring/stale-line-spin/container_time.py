"""Time the worker - the whole graded set, fresh nonce - inside the verifier image at one CPU.

The task grants one CPU (task.toml), and the 60-second clock in tests/test.sh covers the worker,
so this is the number the limit is measured against: the worker, as the sandbox user, over the
submitted six files laid on the pristine tree, exactly as test.sh runs it but without the clock.
Build the images first (python3 tools/docker_trial.py stale-line-spin --build).

usage: python3 authoring/stale-line-spin/container_time.py <dir-with-six-files> [runs]
"""
import pathlib
import subprocess
import sys

IMAGE = "stale-line-spin-test:local"
INNER = r"""
set -e
mkdir -p /app/sim /work
cp /sub/line.py /sub/mem.py /sub/place.py /sub/turn.py /sub/step.py /sub/clock.py /app/sim/
chmod -R a+rX /app
python3 -c "import secrets; print(secrets.token_hex(16))" > /work/nonce
echo 40 > /work/per
chown -R 1002:1002 /work
s=$(date +%s.%N)
setpriv --reuid=1002 --regid=1002 --clear-groups python3 /tests/worker.py --out /work/o.json
e=$(date +%s.%N)
python3 - "$s" "$e" <<'EOF'
import json, sys
recs = json.load(open("/work/o.json"))
bad = sum(1 for r in recs if r["got"] is None)
print("WORKER %.2f s, %d launches, %d raised" % (float(sys.argv[2]) - float(sys.argv[1]), len(recs), bad))
EOF
"""


def main():
    src = pathlib.Path(sys.argv[1]).resolve()
    runs = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    for _ in range(runs):
        p = subprocess.run(["docker", "run", "--rm", "--cpus=1", "-v", "%s:/sub:ro" % src,
                            IMAGE, "bash", "-c", INNER], capture_output=True, text=True)
        line = [x for x in p.stdout.splitlines() if x.startswith("WORKER")]
        print(src.name, line[0] if line else "FAILED " + (p.stderr or p.stdout)[-400:], flush=True)


if __name__ == "__main__":
    main()
