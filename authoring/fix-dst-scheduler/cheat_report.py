"""Which layer catches which cheat.

A cheat that scores 0 for its own reasons proves nothing: the layer report is
what says the attestation, the frozen-file check or the population actually
fired. This runs every cheat through the two-container trial, keeps the
verifier's log, and names the tests that failed. It also runs the isolation
facts directly as the worker uid, so `probe-privilege` and `probe-read-answers`
are backed by the permission errors themselves and not only by a zero.

    python cheat_report.py [name-fragment ...]
"""

import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "tools"))
sys.path.insert(0, HERE)

import docker_trial  # noqa: E402
import harness  # noqa: E402

CHEATS = os.path.join(harness.TASK, "cheat")

FACTS = r"""
import os, sys
rows = []
rows.append("uid=%d" % os.getuid())
for p in ("/logs/verifier/reward.txt", "/tests/gt.json", "/tests/seal/model.py",
          "/tests/test_outputs.py", "/work/run/out.json", "/work/app/sked/emit.py"):
    try:
        open(p).read()
        rows.append("READ OK   " + p)
    except Exception as exc:
        rows.append("read %-14s %s" % (type(exc).__name__, p))
    try:
        open(p, "a").close()
        rows.append("WRITE OK  " + p)
    except Exception as exc:
        rows.append("write %-13s %s" % (type(exc).__name__, p))
print("\n".join(rows))
"""


class Loud(docker_trial.Trial):
    """The same trial, with the verifier's log kept instead of tailed."""

    def verifier_run(self, artdir):
        parents = sorted({str(os.path.join("/app", a)).rsplit("/", 1)[0] for a in self.arts})
        cmd = (
            "mkdir -p %s ; cp -a /artifacts/. /app/ 2>/dev/null ; mkdir -p /logs/verifier ; "
            "bash /tests/test.sh > /tmp/v.log 2>&1 ; "
            "echo REWARD=$(cat /logs/verifier/reward.txt 2>/dev/null) ; cat /tmp/v.log"
        ) % " ".join(parents)
        proc = docker_trial.sh(
            ["docker", "run", "--rm", "-v", "%s:/artifacts:ro" % os.path.abspath(artdir),
             self.test_img, "bash", "-c", cmd])
        reward = 0
        for line in proc.stdout.splitlines():
            if line.startswith("REWARD="):
                try:
                    reward = int(line.split("=", 1)[1].strip() or 0)
                except ValueError:
                    reward = 0
        return reward, proc.stdout

    def probe(self, name, cheat):
        tmp = tempfile.mkdtemp()
        try:
            self.agent_run(Path(cheat), Path(tmp) / "art")
            return self.verifier_run(Path(tmp) / "art")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)


def caught_by(log):
    names = re.findall(r"^FAILED [^:]+::(\S+)", log, re.M)
    if not names:
        names = re.findall(r"^\S*::(\S+) FAILED", log, re.M)
    if not names and "the worker" in log:
        names = ["worker did not report"]
    if not names:
        head = [ln for ln in log.splitlines() if "Error" in ln or "error" in ln]
        names = head[:1] or ["<no test named>"]
    return sorted(set(names))


def isolation_facts(trial):
    """Run the permission probe as the worker uid inside the verifier image."""
    script = "/tmp/facts.py"
    cmd = (
        "mkdir -p /app/sked /logs/verifier ; bash -c 'true' ; "
        "install -d -m 700 -o root -g root /logs/verifier ; echo 0 > /logs/verifier/reward.txt ; "
        "chmod 700 /tests/seal ; chmod 600 /tests/gt.json /tests/seal/model.py "
        "/tests/test_outputs.py ; "
        "rm -rf /work ; mkdir -p /work/app /work/run ; cp -a /pristine/. /work/app/ ; "
        "chown -R root:root /work ; chmod -R u=rwX,go=rX /work/app ; "
        ": > /work/run/out.json ; chmod 600 /work/run/out.json ; "
        "cat > %s <<'PYEOF'\n%s\nPYEOF\n"
        "setpriv --reuid=1004 --regid=1004 --clear-groups python %s"
    ) % (script, FACTS, script)
    proc = docker_trial.sh(["docker", "run", "--rm", trial.test_img, "bash", "-c", cmd])
    return proc.stdout.strip() or proc.stderr.strip()


def main():
    want = sys.argv[1:]
    trial = Loud("fix-dst-scheduler")
    if trial.build() != 0:
        return 1
    print("== isolation facts, as the worker uid ==")
    facts = isolation_facts(trial)
    print(facts)
    bad_facts = [ln for ln in facts.splitlines() if "OK" in ln and "emit.py" not in ln]
    if bad_facts:
        print("REACHABLE FROM THE RUN: %s" % bad_facts)

    rows = []
    for f in sorted(os.listdir(CHEATS)):
        if not (f.startswith("cheat-") and f.endswith(".sh")):
            continue
        if want and not any(w in f for w in want):
            continue
        reward, log = trial.probe(f, os.path.join(CHEATS, f))
        rows.append((f, reward, caught_by(log)))

    print("\n%-38s %6s  %s" % ("cheat", "reward", "caught by"))
    loose = []
    for name, reward, names in rows:
        print("%-38s %6d  %s" % (name, reward, ", ".join(names)[:110]))
        if reward != 0:
            loose.append(name)
        elif names == ["<no test named>"]:
            loose.append(name + " (scored 0 but no test named it)")
    print("\n%d cheats, %d scored 1 or were caught by nothing" % (len(rows), len(loose)))
    for name in loose:
        print("  LOOSE %s" % name)
    return 1 if loose or bad_facts else 0


sys.exit(main())
