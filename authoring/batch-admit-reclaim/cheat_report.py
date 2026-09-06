"""Run every cheat and say which test caught it, not merely that one did.

A suite where every cheat scores 0 proves less than it looks: a cheat caught by
the wrong test is a cheat that would survive a change to the test that was
supposed to catch it. So each row names the tests that failed, and the
attestation probes are additionally required to be caught by their own layer.

This runs the policy payloads on the host. The agent-side probes - the reward
channel, the leftover process, the rewritten frozen file - do nothing here
because there is no second container; tools/docker_trial.py is what exercises
those, and this report says so rather than implying otherwise.

Usage: python3 authoring/batch-admit-reclaim/cheat_report.py
"""

import os
import re
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
TASK = os.path.join(ROOT, "tasks", "batch-admit-reclaim")
TESTS = os.path.join(TASK, "tests")
CHEAT = os.path.join(TASK, "cheat")
WORK = os.environ.get("WORK", "/tmp/bar-work")
POLICY = ("fit.py", "room.py", "back.py", "pick.py")

OWN = {
    "cheat-attest-swap-the-emitter": "test_the_sealed_functions_are_the_pristine_ones",
    "cheat-attest-swap-a-sealed-function": "test_the_sealed_functions_are_the_pristine_ones",
    "cheat-attest-disarm-the-counter": "test_every_line_came_through_the_emitter",
    "cheat-attest-write-the-timeline": "test_the_run_played_every_trace",
}

AGENT_SIDE = ("cheat-probe-reward-channel", "cheat-probe-sweep",
              "cheat-probe-rewrite-frozen", "cheat-probe-read-truth")


def carve(text):
    out = {}
    for name in POLICY:
        pat = r"cat > /app/eng/%s <<'POLICY_EOF'\n(.*?)POLICY_EOF\n" % re.escape(name)
        found = re.search(pat, text, re.S)
        if found:
            out[name] = found.group(1)
    return out


def grade(files):
    box = os.path.join(WORK, "cheatbox")
    app = os.path.join(box, "app")
    if os.path.isdir(box):
        shutil.rmtree(box)
    os.makedirs(box)
    shutil.copytree(os.path.join(TESTS, "pristine"), app)
    for name, text in files.items():
        with open(os.path.join(app, "eng", name), "w") as handle:
            handle.write(text)
    out = os.path.join(box, "out.json")
    nonce = os.urandom(32).hex()
    env = dict(os.environ)
    env.update({"APPDIR": app, "RUN_NONCE": nonce, "RUN_COUNT": "300",
                "PYTHONDONTWRITEBYTECODE": "1"})
    subprocess.run([sys.executable, os.path.join(TESTS, "runner.py"), out],
                   env=env, capture_output=True, text=True)
    env.update({"RUN_OUT": out, "APP_DIR": app,
                "PRISTINE_DIR": os.path.join(TESTS, "pristine"),
                "PYTHONPATH": TESTS})
    run = subprocess.run(["python3", "-m", "pytest", "-q", "--no-header", "-rf",
                          os.path.join(TESTS, "test_outputs.py")],
                         env=env, capture_output=True, text=True)
    failed = sorted(set(re.findall(r"FAILED .*::(\w+)", run.stdout)))
    return (1 if run.returncode == 0 else 0), failed


def main():
    names = sorted(p[:-3] for p in os.listdir(CHEAT) if p.endswith(".sh"))
    width = max(len(n) for n in names)
    bad = 0
    for name in names:
        with open(os.path.join(CHEAT, name + ".sh")) as handle:
            files = carve(handle.read())
        score, failed = grade(files)
        note = ",".join(f.replace("test_", "") for f in failed) or "-"
        flag = ""
        if score != 0:
            if name in AGENT_SIDE:
                note = "host emulation cannot run this one; see docker_trial"
            else:
                flag = "  SCORED 1"
                bad += 1
        want = OWN.get(name)
        if want and want not in failed:
            flag += "  NOT CAUGHT BY ITS OWN LAYER (%s)" % want
            bad += 1
        if want and [f for f in failed if f not in (want, "test_the_run_played_every_trace")]:
            flag += "  ALSO CAUGHT BY %s" % [f for f in failed if f != want]
        print("  %-*s  %d  %s%s" % (width, name, score, note, flag))
    print("%d cheats, %d findings" % (len(names), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
