#!/usr/bin/env python3
"""What the isolation probes are actually proving, asserted at the layer. Never ships.

A probe that scores 0 has proved nothing on its own: the run it sits on scores 0 anyway. What
makes it evidence is that the attack was denied, so this checks the denial directly, as the
sandbox uid, against the staging `host_trial.py` leaves behind.

Run it straight after a probe trial:

    python3 -u authoring/lock-cover-wake/host_trial.py tasks/lock-cover-wake/cheat/cheat-probe-privilege.sh
    python3 -u authoring/lock-cover-wake/isolation.py
"""
import os
import subprocess
import sys

UID = 1002


def as_sandbox(code):
    return subprocess.run(["setpriv", "--reuid=%d" % UID, "--regid=%d" % UID, "--clear-groups",
                           "python3", "-c", code], capture_output=True, text=True)


def main():
    bad = 0
    st = os.stat("/logs/verifier")
    print("reward directory: mode %o owner %d" % (st.st_mode & 0o777, st.st_uid))
    if (st.st_mode & 0o777) != 0o700 or st.st_uid != 0:
        print("   FINDING the reward channel is not root-owned 0700")
        bad += 1

    st = os.stat("/tests/seal")
    print("sealed directory: mode %o owner %d" % (st.st_mode & 0o777, st.st_uid))
    if (st.st_mode & 0o777) != 0o700 or st.st_uid != 0:
        print("   FINDING the sealed model is not root-owned 0700")
        bad += 1

    reward = open("/logs/verifier/reward.txt").read().strip()
    print("reward left behind: %r" % reward)

    for what, code in (
        ("read the frozen answers",
         "open('/tests/seal/gt.json').read()"),
        ("read the sealed model",
         "open('/tests/seal/model.py').read()"),
        ("write the reward",
         "open('/logs/verifier/reward.txt','w').write('1')"),
        ("rewrite the grader",
         "open('/tests/test_outputs.py','w').write('')"),
        ("rewrite the generator",
         "open('/tests/gen.py','w').write('')"),
        ("read the authoritative seed",
         "open('/logs/verifier/nonce').read()"),
    ):
        done = as_sandbox(code)
        line = done.stderr.strip().splitlines()[-1:] or ["no error"]
        ok = done.returncode != 0 and "PermissionError" in line[0]
        print("   %-28s %s  %s" % (what, "denied" if ok else "ALLOWED", line[0][:60]))
        if not ok:
            bad += 1
    print("\n%d findings" % bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
