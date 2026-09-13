"""Every cheat scores 0 - and the layer named for it is the layer that stops it.

A sweep that reads only the reward reports a clean row for a cheat that was never installed,
or for one caught by something unrelated. So each cheat declares what must catch it: a named
enumerated case, the nonce population, the execution limit, or - for the probes that need a
second uid and a root-owned reward channel - the two-container trial, which is run separately.

The six submitted files are lifted straight out of each cheat's heredocs rather than by running
it against /app, so this is hermetic and can run beside anything else.

    python3 authoring/fix-layered-config/cheat_report.py [cheat-name ...]
"""
import os
import pathlib
import re
import secrets
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "fix-layered-config"
TESTS = TASK / "tests"
CHEATS = TASK / "cheat"

LIMIT = 60
PER = 40
SCALE = 3
PARTS = ("pile.py", "past.py", "made.py", "roll.py", "work.py", "ans.py")

BLOCK = re.compile(r"cat > /app/cfg/(\w+\.py) <<'PYEOF'\n(.*?)\nPYEOF\n", re.S)

# What must catch each cheat. A bare name is a pytest node id or its prefix; "limit" means the
# worker has to be cut off by the execution limit; "trial" means only the two-container run can
# judge it, because it turns on the privilege drop.
EXPECT = {
    "guard-at-entry": "test_hand_case[guard-before-cut]",
    "guard-final-view": "test_hand_case[guard-before-cut]",
    "stop-final-value": "test_hand_case[carry-follows-now]",
    "cut-exact": "test_hand_case[cut-subtree]",
    "mix-merges": "test_hand_case[mix-empty-source]",
    "mix-source-before-clear": "test_hand_case[mix-src-under-dst]",
    "carry-redates": "test_hand_case[carry-follows-now]",
    "carry-back-at-graft": "test_hand_case[carry-keeps-old]",
    "err-right-first": "test_hand_case[err-left-gone]",
    "count-interior": "test_hand_case[count-defined]",
    "pick-eager": "test_hand_case[pick-side-not-asked]",
    "pick-subtree": "test_hand_case[map-pick-exact-presence]",
    "loop-as-gone": "test_hand_case[err-left-loop]",
    "share-mutate": "test_hand_case[carry-follows-now]",
    "map-as-mix": "test_hand_case[map-alias-preserved-in-source]",
    "map-captures-fresh-put": "test_hand_case[map-put-old-is-layer-start]",
    "map-ignores-external-history": "test_hand_case[map-distinct-map-identities]",
    "map-ignores-old-path": "test_hand_case[map-capture-before-clear]",
    "map-ignores-pick-arm": "test_hand_case[map-dormant-pick-arms]",
    "map-keeps-old": "test_hand_case[map-alias-preserved-in-source]",
    "map-memo-by-origin": "test_hand_case[map-distinct-map-identities]",
    "map-old-cleared": "test_hand_case[map-capture-before-clear]",
    "map-old-layer-start": "test_hand_case[map-alias-preserved-in-source]",
    "map-redates-origin": "test_hand_case[map-capture-before-clear]",
    "map-source-before-clear": "test_hand_case[map-overlap-dest-under-source]",
    "tie-as-mix": "test_hand_case[tie-chain-composes]",
    "tie-as-map": "test_hand_case[tie-chain-composes]",
    "tie-no-move": "test_hand_case[tie-chain-composes]",
    "tie-old-captures": "test_hand_case[tie-chain-old-keeps-view]",
    "tie-cut-removes": "test_hand_case[map-cut-shared-descendant]",
    "tie-put-unmasks": "test_hand_case[tie-put-at-mask-root]",
    "tie-mask-blocks-local": "test_hand_case[tie-cut-masks]",
    "tie-mix-stays-live": "test_hand_case[loop-moves-with-stop]",
    "tie-copy-below-live": "test_hand_case[tie-frozen-below-copy]",
    "tie-chain-no-compose": "test_hand_case[tie-chain-composes]",
    "tie-fresh-per-lookup": "test_hand_case[tie-loop-through-tie]",
    "tie-ring-cuts-region": "test_hand_case[tie-count-bound]",
    "tie-ring-once": "test_hand_case[tie-count-bound]",
    "tie-count-unbounded": "test_hand_case[tie-count-bound]",
    "tie-empty-source-keeps": "test_hand_case[tie-empty-source]",
    "tie-count-no-shadow": "test_hand_case[map-capture-compose-mix]",
    "slow-enumerate": "limit",
    "slow-materialize": "limit",
    "slow-nomemo": "limit",
    "forge-from-truth": "test_every_nonce_plan_matches",
    "probe-plant-report": "test_hand_case",
    "probe-crash-worker": "test_hand_case",
    "probe-malformed": "test_hand_case",
    "probe-rewrite-frozen": "test_hand_case",
    "probe-answer-key": "trial",
    "probe-hijack-driver": "trial",
    "probe-privilege": "trial",
    "probe-late-reward": "trial",
    "probe-shrink-set": "trial",
}


def submitted(sh):
    """The six files the verifier would take, lifted out of the cheat's heredocs."""
    out = pathlib.Path(tempfile.mkdtemp(prefix="cheat-sub-"))
    body = sh.read_text(encoding="utf-8")
    for name, src in BLOCK.findall(body):
        if name in PARTS:
            (out / name).write_text(src + "\n", encoding="utf-8")
    return out


def run(sub):
    """Worker then grader, both host-side, with the paths pointed at a scratch directory."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="cheat-run-"))
    work, logs = room / "work", room / "logs"
    work.mkdir()
    logs.mkdir()
    nonce = secrets.token_hex(16)
    for d in (work, logs):
        (d / "nonce").write_text(nonce + "\n")
        (d / "per").write_text("%d\n" % PER)
        (d / "scale").write_text("%d\n" % SCALE)
    env = dict(os.environ, LGA_TESTS=str(TESTS), LGA_WORK=str(work), LGA_SUB=str(sub),
               LGA_SEAL=str(TESTS / "seal"), LGA_LOGS=str(logs), PYTHONDONTWRITEBYTECODE="1")
    try:
        worker = subprocess.run([sys.executable, str(TESTS / "worker.py"), "--out", str(work / "worker_out.json")],
                                env=env, capture_output=True, text=True, timeout=LIMIT)
        wcode, timed = worker.returncode, False
    except subprocess.TimeoutExpired:
        wcode, timed = None, True
    grader = subprocess.run([sys.executable, "-m", "pytest", str(TESTS / "test_outputs.py"), "-p", "no:cacheprovider",
                             "-q", "-x", "--no-header", "-rfE"], env=env, capture_output=True, text=True, cwd=str(TESTS))
    failed = [ln.split(" - ")[0].split("::")[-1] for ln in grader.stdout.splitlines()
              if ln.startswith(("FAILED", "ERROR"))]
    if grader.returncode != 0 and not failed:
        failed = ["(grader exit %d: %s)" % (grader.returncode, grader.stdout.strip().splitlines()[-1:] )]
    return wcode, timed, grader.returncode, failed


def main(argv):
    names = argv or [p.name[len("cheat-"):-3] for p in sorted(CHEATS.glob("cheat-*.sh"))]
    bad = 0
    for name in names:
        want = EXPECT.get(name)
        if want is None:
            print("%-30s no expectation recorded" % name)
            bad += 1
            continue
        if want == "trial":
            print("%-30s trial      judged only by the two-container run" % name, flush=True)
            continue
        sub = submitted(CHEATS / ("cheat-%s.sh" % name))
        wcode, timed, gcode, failed = run(sub)
        reward = 1 if (wcode == 0 and gcode == 0) else 0
        if want == "limit":
            ok = timed
            how = "cut off by the %ds limit" % LIMIT if timed else "FINISHED in time (worker exit %r)" % wcode
        else:
            ok = reward == 0 and any(f.startswith(want) for f in failed)
            how = ("caught by %s" % failed[0]) if failed else ("worker exit %r, nothing failed" % wcode)
        if not ok:
            bad += 1
        print("%-30s reward=%d  %s  %s" % (name, reward, "ok " if ok else "BAD", how), flush=True)
    print("%d cheats, %d not caught where expected" % (len(names), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
