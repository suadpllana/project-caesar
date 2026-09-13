"""Run every cheat in the two containers and record what caught it, not just the reward.

A cheat that scores 0 for a reason other than the one it was written to probe is a cheat
that proves nothing. So this records the worker's exit status and the pytest tests that
failed, and checks each one against the layer the cheat is supposed to hit: an enumerated
case, the nonce population, the execution limit, or the isolation.
"""
import json
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path("/home/user/project-caesar")
TASK = ROOT / "tasks" / "anchor-mean-settle"
ENV = "anchor-mean-settle-env:local"
TST = "anchor-mean-settle-test:local"
PARTS = ("grid.py", "gues.py", "seat.py", "step.py", "edit.py", "ask.py")

# cheat name -> the layer that must catch it
LAYER = {
    "slow-walk": "limit", "slow-rebuild": "limit",
    "forge-from-truth": "nonce",
}
PROBES = ("probe-answer-key", "probe-plant-report", "probe-crash-after-plant",
          "probe-malformed", "probe-privilege", "probe-shrink-set", "probe-late-reward")

# Every probe is laid over a panel that does not do the work, so a reward of 1 can only come
# from the attack. What must also be true is that the attack was attempted and denied, which
# the reward alone does not say: each probe shouts a distinctive line if its attack lands, and
# each leaves a distinctive trace when it does not.
LOUD = ("SEAL-READABLE", "VERIFIER-WRITABLE", "VERIFIER-ROOT", "TESTS-WRITABLE")
DENIED = {
    "probe-answer-key": "DENIED seal PermissionError",
    "probe-privilege": "DENIED /logs/verifier/reward.txt PermissionError",
    "probe-shrink-set": "DENIED /tests/gen.py PermissionError",
    "probe-plant-report": "DENIED reward PermissionError",
    "probe-late-reward": "reaped 1",
    "probe-crash-after-plant": "no result for hand case",
    "probe-malformed": "worker output is not a list",
}


def sh(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def one(script):
    art = pathlib.Path(tempfile.mkdtemp(prefix="ams-art-"))
    # mkdtemp is 700, and `cp -a` carries that onto /app/pan in the verifier, where
    # the unprivileged worker then cannot traverse it. That is this harness, not the task.
    art.chmod(0o755)
    try:
        collect = " ; ".join(
            "if [ -f /app/pan/%s ]; then mkdir -p /out/pan; cp /app/pan/%s /out/pan/%s; fi"
            % (p, p, p) for p in PARTS)
        inner = "true" if script is None else "bash /agent.sh >/tmp/a.log 2>&1 || true"
        mounts = [] if script is None else ["-v", "%s:/agent.sh:ro" % script]
        sh(["docker", "run", "--rm", "-v", "%s:/out" % art] + mounts
           + [ENV, "bash", "-c", "%s ; %s" % (inner, collect)])
        cmd = ("mkdir -p /app/pan ; cp -a /artifacts/. /app/ 2>/dev/null ; "
               "mkdir -p /logs/verifier ; bash /tests/test.sh > /tmp/v.log 2>&1 ; "
               "echo ---REWARD=$(cat /logs/verifier/reward.txt 2>/dev/null) ; cat /tmp/v.log")
        out = sh(["docker", "run", "--rm", "-v", "%s:/artifacts:ro" % art, TST,
                  "bash", "-c", cmd]).stdout
    finally:
        shutil.rmtree(art, ignore_errors=True)
    reward = 0
    m = re.search(r"---REWARD=(\d+)", out)
    if m:
        reward = int(m.group(1))
    worker = None
    m = re.search(r"worker exit (\d+)", out)
    if m:
        worker = int(m.group(1))
    failed = sorted(set(re.findall(r"(test_\w+)(?:\[([^\]]+)\])?\s*[-_]*\s*(?:assert|Failed|$)",
                                   out)) )
    names = sorted(set(re.findall(r"FAILED[^:]*::(\w+)(?:\[([^\]]*)\])?", out)))
    short = sorted(set(re.findall(r"^(test_\w+)\[?([^\]\s]*)\]?", out, re.M)))
    return reward, worker, out, names or short


def layer_of(out, names, worker):
    hand = [n for n in names if n[0] == "test_hand_case"]
    nonce = any(n[0] == "test_every_nonce_program_matches" for n in names)
    fams = any(n[0] == "test_every_family_is_represented" for n in names)
    if worker not in (0, None):
        return "limit" if worker == 124 else "worker exit %s" % worker
    if hand:
        return "hand:" + hand[0][1]
    if fams:
        return "families"
    if nonce:
        return "nonce"
    return "unclear"


def main():
    picks = sys.argv[1:]
    rows = []
    for script in sorted((TASK / "cheat").glob("cheat-*.sh")):
        name = script.stem[len("cheat-"):]
        if picks and name not in picks:
            continue
        reward, worker, out, names = one(str(script))
        got = layer_of(out, names, worker)
        want = LAYER.get(name, "hand" if name not in PROBES else "any")
        ok = reward == 0
        if name in PROBES:
            loud = [m for m in LOUD if m in out]
            need = DENIED.get(name)
            ok = ok and not loud and (need is None or need in out)
            got = ("ATTACK LANDED: %s" % loud[0]) if loud else (
                "denied (%s)" % need if need else got)
        elif want == "limit":
            ok = ok and got == "limit"
        elif want == "nonce":
            ok = ok and got == "nonce"
        elif want == "hand":
            ok = ok and got.startswith("hand:")
        rows.append((name, reward, worker, got, ok))
        print("%-26s reward=%d worker=%s caught by %-22s %s"
              % (name, reward, worker, got, "ok" if ok else "<-- WRONG LAYER"), flush=True)
        if not ok and "--v" in picks:
            print(out[-3000:])
    bad = [r[0] for r in rows if not r[4]]
    print()
    print("%d cheats, %d scored 0 at the layer they were written for" % (len(rows), len(rows) - len(bad)))
    if bad:
        print("wrong:", bad)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
