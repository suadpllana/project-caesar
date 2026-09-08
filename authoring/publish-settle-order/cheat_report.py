"""Every cheat scores 0 - and the layer named for it is the layer that stops it.

A sweep that reads only the reward reports a clean row for a cheat that was never installed, or
for one caught by something unrelated. So each cheat declares what must catch it: a named
enumerated case, the nonce population, the execution limit, or - for the probes that need a
second uid and a root-owned reward channel - the two-container trial, which is run separately.

The five submitted files are lifted straight out of each cheat's heredocs rather than by running
it against `/app`, so this is hermetic and can run beside anything else.

    python3 authoring/publish-settle-order/cheat_report.py
"""
import os
import pathlib
import re
import secrets
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "publish-settle-order"
TESTS = TASK / "tests"
CHEATS = TASK / "cheat"

LIMIT = 60
PER = 60
PARTS = ("walk.py", "pick.py", "site.py", "want.py", "drop.py")

BLOCK = re.compile(r"cat > /app/link/(\w+\.py) <<'PYEOF'\n(.*?)\nPYEOF\n", re.S)

# What must catch each cheat. A bare name is a pytest node id or its prefix; "limit" means the
# worker has to be cut off by the execution limit; "trial" means only the two-container run can
# judge it, because it turns on the privilege drop.
EXPECT = {
    "boot-before-publish": "test_hand_case[boot-cycle]",
    "boots-after-closure": "test_hand_case[boot-cycle]",
    "call-when-down": "test_hand_case[not-live]",
    "dead-rebinds": "test_hand_case[boot-cycle]",
    "deps-need-not-live": "test_hand_case[casc-order]",
    "fallback-always": "test_hand_case[fall-late]",
    "holds-only": "test_hand_case[dep-holds]",
    "needs-sorted": "test_hand_case[dep-order]",
    "newest-publisher": "test_hand_case[fall-first]",
    "pre-after-deps": "test_hand_case[pre-order]",
    "pre-skipped": "test_hand_case[pre-no-keep]",
    "rel-any-unit": "test_hand_case[rel-early]",
    "resolve-each-call": "test_hand_case[dead-stays]",
    "reup-moves": "test_hand_case[stay-put]",
    "reup-no-hold": "test_hand_case[casc-part]",
    "same-name-same-unit": "test_hand_case[same-name]",
    "settle-the-miss": "test_hand_case[boot-partial]",
    "soft-keeps": "test_hand_case[pre-no-keep]",
    "strong-over-fallback": "test_hand_case[fall-first]",
    "sweep-forward": "test_hand_case[casc-order]",
    "sweep-once": "test_hand_case[casc-order]",
    "uses-survive": "test_hand_case[fresh-instance]",
    "scan-the-order": "limit",
    "scan-cached": "limit",
    "rebuild-each-change": "limit",
    "forge-from-truth": "test_every_nonce_program_matches",
    "probe-plant-verdict": "test_hand_case",
    "probe-crash-worker": "test_hand_case",
    "probe-malformed": "test_hand_case",
    "probe-rewrite-frozen": "test_hand_case",
    "probe-answer-key": "trial",
    "probe-hijack-driver": "trial",
    "probe-privilege": "trial",
    "probe-late-reward": "trial",
    "probe-forge-report": "trial",
    "probe-shrink-set": "trial",
}


def submitted(sh):
    """The five files the verifier would take, lifted out of the cheat's heredocs."""
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
        (d / "nonce").write_text(nonce + "\n", encoding="utf-8")
        (d / "per").write_text("%d\n" % PER, encoding="utf-8")
    env = dict(os.environ)
    env.update({"PSO_TESTS": str(TESTS), "PSO_WORK": str(work), "PSO_LOGS": str(logs),
                "PSO_SEAL": str(TESTS / "seal"), "PSO_SUB": str(sub),
                "PYTHONDONTWRITEBYTECODE": "1"})
    try:
        w = subprocess.run([sys.executable, str(TESTS / "worker.py"),
                            "--out", str(work / "worker_out.json")],
                           env=env, capture_output=True, text=True, timeout=LIMIT)
        rc = w.returncode
    except subprocess.TimeoutExpired:
        rc = 124
    g = subprocess.run([sys.executable, "-m", "pytest", str(TESTS / "test_outputs.py"),
                        "-p", "no:cacheprovider", "-q", "--tb=no", "-rfE"],
                       env=env, capture_output=True, text=True, timeout=1800)
    bad = []
    for line in g.stdout.splitlines():
        m = re.match(r"^(FAILED|ERROR) \S*::(\S+)", line.strip())
        if m:
            bad.append(m.group(2))
    return rc, bad, g.returncode


def main():
    rows, wrong = [], 0
    for sh in sorted(CHEATS.glob("cheat-*.sh")):
        name = sh.stem[len("cheat-"):]
        want = EXPECT.get(name)
        if want is None:
            print("   %-24s NO EXPECTATION - add it to EXPECT" % name)
            wrong += 1
            continue
        if want == "trial":
            rows.append("   %-24s left to the two-container trial (privilege drop)" % name)
            continue
        sub = submitted(sh)
        rc, bad, graded = run(sub)
        if want == "limit":
            ok = rc == 124
            rows.append("   %-24s worker rc=%d %s" % (name, rc, "cut off by the limit" if ok else "NOT CUT OFF"))
        else:
            ok = graded != 0 and any(b == want or b.startswith(want) for b in bad)
            rows.append("   %-24s %s <- %s" % (name, "caught" if ok else "NOT CAUGHT BY " + want,
                                               ", ".join(sorted(bad)[:3]) or "nothing failed"))
        if not ok:
            wrong += 1
    print("== publish-settle-order cheat layers")
    for r in rows:
        print(r)
    print("   %d of %d cheats caught by the layer named for them"
          % (len(rows) - wrong, len(rows)))
    return 1 if wrong else 0


if __name__ == "__main__":
    sys.exit(main())
