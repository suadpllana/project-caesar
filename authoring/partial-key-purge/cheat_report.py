"""Run every cheat through the real two-container trial and assert the layer that catches it.

Authoring only. CLAUDE.md: a sweep that only checks the reward reports a clean zero for a cheat
that was never installed, so every row here asserts *why* the cheat scored 0:

  wrong readings   the hand case readingcheck named as separating it is among the failures
  forgery          carries every frozen hand answer, passes every hand case, fails the nonce set
  shortcuts        at least one hand case fails
  replay audit     every hand case passes and the worker is stopped by the wall clock
  probes           the probe's own notes show the attack was refused (or, for the late writer,
                   reaped), and nothing it wrote reached the reward

The agent image runs the cheat script, the declared files are collected, and the verifier
image runs tests/test.sh under the declared caps (1 CPU, 2 GB), as tools/docker_trial.py does.
Images must already be built (local_trial.py builds them).

    python -u cheat_report.py [name-substring ...]
"""
import concurrent.futures
import os
import re
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
TASK = os.path.normpath(os.path.join(HERE, "..", "..", "tasks", "partial-key-purge"))
ENV_IMG = "partial-key-purge-env:local"
TEST_IMG = "partial-key-purge-test:local"
PARTS = ("match.py", "drop.py", "clear.py", "hold.py", "audit.py")

SEPARATES = {
    "audit-retained-set": "audit-loop",
    "audit-sums-children": "audit-diamond",
    "cleared-only-if-changed": "setnull-already-null",
    "depth-at-fifteen": "depth-limit",
    "depth-fails-first-ref-only": "depth-both-refs",
    "descendant-reach": "merge-wild-side",
    "end-check-before-clearing": "restrict-broken-by-clear",
    "fork-needs-both": "merge-either",
    "full-half-null-accepted": "full-broken-by-clear",
    "held-counts-zero": "audit-names",
    "key-null-allowed": "setnull-key-column",
    "loops-always-keep": "or-loop-broken",
    "name-by-row-first": "order-decl",
    "named-not-counted": "audit-diamond",
    "no-depth-limit": "depth-limit",
    "no-self-match": "self-restrict",
    "noaction-as-restrict": "noaction-removed-anyway",
    "reachability-frees-loops": "audit-loop",
    "restrict-as-noaction": "restrict-removed-anyway",
    "restrict-only-by-losing": "restrict-broken-by-clear",
    "rounds-longest-path": "depth-merge-shortcut",
    "row-by-row-clear-feeds-back": "clear-no-feedback",
    "setnull-clears-all": "full-broken-by-clear",
    "simple-for-all": "audit-diamond",
    "tree-audit": "merge-either",
}
SHORTCUTS = ("constant", "named-only", "refuse-first", "example-replayed")


def sh(cmd, timeout=1800):
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def trial(cheat):
    room = tempfile.mkdtemp(prefix="pkp-cheat-")
    try:
        collect = " ; ".join("if [ -f /app/db/%s ]; then mkdir -p /out/db; cp /app/db/%s /out/db/%s; fi"
                             % (p, p, p) for p in PARTS)
        sh(["docker", "run", "--rm", "-v", "%s:/out" % room, "-v", "%s:/agent.sh:ro" % cheat,
            ENV_IMG, "bash", "-c", "bash /agent.sh >/tmp/agent.log 2>&1 || true ; " + collect])
        inner = ("mkdir -p /app/db ; cp -a /artifacts/. /app/ 2>/dev/null ; "
                 "bash /tests/test.sh > /tmp/v.log 2>&1 ; cat /tmp/v.log ; "
                 "echo ===PROBE ; cat /work/run/probe.log 2>/dev/null ; "
                 "echo ===REWARD $(cat /logs/verifier/reward.txt)")
        got = sh(["docker", "run", "--rm", "--cpus", "1", "--memory", "2g",
                  "-v", "%s:/artifacts:ro" % room, TEST_IMG, "bash", "-c", inner])
        return got.stdout
    finally:
        shutil.rmtree(room, ignore_errors=True)


def judge(name, log):
    reward = re.search(r"===REWARD (\d)", log)
    reward = int(reward.group(1)) if reward else -1
    failed = set(re.findall(r"FAILED \S*test_hand_case\[([^\]]+)\]", log))
    errors = len(re.findall(r"^ERROR ", log, re.M))
    worker = re.search(r"worker exit (-?\d+)", log)
    worker = int(worker.group(1)) if worker else None
    reaped = re.search(r"reaped (\d+)", log)
    reaped = int(reaped.group(1)) if reaped else 0
    probe = log.split("===PROBE", 1)[1].split("===REWARD", 1)[0] if "===PROBE" in log else ""
    nonce_bad = "nonce scripts wrong" in log or "test_every_nonce_script_matches" in log and "FAILED" in log
    why = []
    ok = reward == 0
    key = name[len("cheat-"):-3]
    if key in SEPARATES:
        want = SEPARATES[key]
        hit = want in failed
        ok = ok and hit
        why.append("hand %s %s" % (want, "fails" if hit else "DID NOT FAIL"))
    elif key in SHORTCUTS:
        ok = ok and bool(failed or errors)
        why.append("%d hand cases fail" % len(failed))
    elif key == "forge-from-truth":
        nonce = "test_every_nonce_script_matches" in log and re.search(r"FAILED \S*test_every_nonce_script_matches", log)
        ok = ok and not failed and bool(nonce)
        why.append("%d hand cases fail (all carried), nonce population %s" % (len(failed), "fails it" if nonce else "DID NOT FAIL"))
    elif key == "replay-audit":
        clock = worker == 124
        ok = ok and clock and not failed
        why.append("worker exit %s%s, %d hand cases fail" % (worker, " (wall clock)" if clock else "", len(failed)))
    elif key.startswith("probe-"):
        denied = probe.count("DENIED")
        bad = [line for line in probe.splitlines() if line.startswith(("FORGED", "WROTE", "GAINED", "REMOVED"))]
        if key == "probe-late-reward":
            lingered = "LINGERING" in probe
            ok = ok and lingered and reaped >= 1
            why.append("lingered %s, reaped %d" % (lingered, reaped))
        elif key == "probe-crash-worker":
            ok = ok and worker not in (0, None) and "KILLED" in probe
            why.append("worker exit %s after the kill" % worker)
        elif key == "probe-malformed-report":
            unreadable = "worker produced no readable output" in log
            ok = ok and unreadable
            bad = []
            why.append("grader %s the corrupted report" % ("refused" if unreadable else "DID NOT REFUSE"))
        elif key in ("probe-malformed", "probe-hijack-driver"):
            ok = ok and bool(failed)
            why.append("%d hand cases fail" % len(failed))
        else:
            ok = ok and denied > 0 and not bad
            why.append("%d denials, %d successes" % (denied, len(bad)))
        if bad:
            why.append("SUCCEEDED: %s" % bad[:3])
    return ok, reward, "; ".join(why)


def main():
    picks = sys.argv[1:]
    cheats = sorted(f for f in os.listdir(os.path.join(TASK, "cheat")) if f.endswith(".sh"))
    if picks:
        cheats = [c for c in cheats if any(p in c for p in picks)]
    results = {}
    with open(os.path.join(HERE, "cheat_report.last"), "w", encoding="utf-8") as f:
        f.write("cheat report, %d cheats\n" % len(cheats))
    with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
        futs = {pool.submit(trial, os.path.join(TASK, "cheat", c)): c for c in cheats}
        for fut in concurrent.futures.as_completed(futs):
            c = futs[fut]
            ok, reward, why = judge(c, fut.result())
            results[c] = ok
            line = "%-44s reward=%d  %s  %s" % (c, reward, "caught as intended" if ok else "WRONG LAYER", why)
            print(line, flush=True)
            with open(os.path.join(HERE, "cheat_report.last"), "a", encoding="utf-8") as f:
                f.write(line + "\n")
    good = sum(results.values())
    print("%d/%d cheats scored 0 for the intended reason" % (good, len(results)))
    return 0 if good == len(results) else 1


if __name__ == "__main__":
    sys.exit(main())
