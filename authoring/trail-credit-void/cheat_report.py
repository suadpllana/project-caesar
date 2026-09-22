"""Run every cheat in the real two containers and say which test caught it.

A cheat sweep that only reads the reward is a sweep that cannot tell "the isolation held" from
"the run fell over for its own reasons" - and a whole sweep once reported eighteen clean zeroes
while never installing the cheat at all (CLAUDE.md, 2026-09-06). So this records the failing
test ids as well, and asserts the expected catcher for every cheat whose catcher is named.

    python cheat_report.py            every cheat
    python cheat_report.py bar-state  just the ones whose name contains this
"""
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

ENV_IMG = "trail-credit-void-env:local"
TEST_IMG = "trail-credit-void-test:local"
ARTS = ["crd/%s" % part for part in lab.PARTS]

# Which enumerated case must be the one that fails, for every cheat that is a wrong reading.
# Taken from tools/readingcheck.py, which measures it rather than assuming it.
CATCHER = {
    "bar-back-any": "bar-back",
    "bar-state": "bar-back",
    "bars-first": "obs-base-silent",
    "bud-per-step": "bud-counts-failed",
    "bud-spares-failed": "bar-err-invisible",
    "close-keeps": "close-next-baseline",
    "close-loses-credit": "bud-cut-step",
    "credit-recompute": "pred-off-zero",
    "err-keeps": "bar-err-invisible",
    "obs-err-too": "bar-err-invisible",
    "obs-per-action": "bar-err-invisible",
    "off-zero": "pred-off-zero",
    "pre-same-obs": "obs-base-silent",
    "rearm-now": "obs-base-silent",
    "rearm-on-touch": "void-rearm-false",
    "rep-count": "close-undo-keeps-credit",
    "rep-full-any": "close-next-baseline",
    "up-strict": "pred-up-equal",
    "void-cone-shut": "void-shut-named",
    "void-named-only": "void-ascending",
    "void-uncredited-skip": "void-uncredited",
    "void-walk-order": "void-ascending",
}

# What must catch everything else. "nonce" means the trails it could not have seen; "any"
# means any failure is proof enough, which is only used where the attack itself is the point.
OTHER = {
    "slow-copy": "clock",
    "slow-sweep": "clock",
    "const-nothing": "hand",
    "const-everything": "hand",
    "pos-replay-example": "hand",
    "forge-hand": "nonce",
    "probe-answer-key": "hand",
    "probe-late-reward": "hand",
    "probe-plant-report": "hand",
    "probe-crash-worker": "any",
    "probe-malformed": "worker",
    "probe-privilege": "hand",
    "probe-rewrite-gen": "hand",
    "probe-shrink-set": "hand",
    "probe-uncollected-file": "any",
}

VERIFY = (
    "mkdir -p /app/crd ; cp -a /artifacts/. /app/ 2>/dev/null ; mkdir -p /logs/verifier ; "
    "bash /tests/test.sh > /tmp/v.log 2>&1 ; "
    "echo REWARD=$(cat /logs/verifier/reward.txt 2>/dev/null) ; cat /tmp/v.log"
)


def one(script):
    room = pathlib.Path(tempfile.mkdtemp())
    art = room / "art"
    art.mkdir()
    try:
        collect = " ; ".join(
            "if [ -f /app/%s ]; then mkdir -p /out/$(dirname %s); cp /app/%s /out/%s; fi"
            % (a, a, a, a) for a in ARTS)
        subprocess.run(
            ["docker", "run", "--rm", "-v", "%s:/out" % art.resolve(),
             "-v", "%s:/agent.sh:ro" % script.resolve(), ENV_IMG, "bash", "-c",
             "bash /agent.sh >/tmp/a.log 2>&1 || true ; %s" % collect],
            capture_output=True, text=True)
        got = subprocess.run(
            ["docker", "run", "--rm", "-v", "%s:/artifacts:ro" % art.resolve(),
             TEST_IMG, "bash", "-c", VERIFY], capture_output=True, text=True)
    finally:
        shutil.rmtree(room, ignore_errors=True)
    text = got.stdout
    reward = 0
    for line in text.splitlines():
        if line.startswith("REWARD="):
            reward = int(line.split("=", 1)[1].strip() or 0)
    # A pytest FAILED means an assertion ran and rejected the submission; an ERROR means a
    # fixture died first, usually because the worker never wrote a record. Telling the two
    # apart is the whole point of this report.
    failed = set(re.findall(r"FAILED [^:]+::([\w\[\]\-]+)", text))
    errored = set(re.findall(r"ERROR [^:]+::([\w\[\]\-]+)", text))
    hand = {m.group(1) for m in re.finditer(r"FAILED [^:]+::test_hand_case\[([\w\-]+)\]", text)}
    timed = "half one exited 124" in text
    blank = "half one exited 0" not in text and not failed and bool(errored)
    nonce = any("nonce" in name for name in failed)
    return reward, failed, hand, timed, nonce, blank, text


def verdict(name, reward, failed, hand, timed, nonce, blank):
    if reward != 0:
        return "SCORED 1"
    want = CATCHER.get(name)
    if want:
        return "caught by %s" % want if want in hand else \
            "NOT CAUGHT by %s (failed: %s)" % (want, sorted(hand)[:3] or sorted(failed)[:3])
    kind = OTHER.get(name, "any")
    if kind == "clock":
        return "worker ran out of its clock" if timed else \
            "NOT the clock (failed: %s)" % (sorted(hand)[:3] or sorted(failed)[:3])
    if kind == "worker":
        return "the worker could not write its record" if blank and not timed else \
            "NOT the worker (failed: %s)" % (sorted(hand)[:3] or sorted(failed)[:3])
    if kind == "hand":
        return "caught by %d hand trails" % len(hand) if hand else \
            "NOT caught by a hand trail (failed: %s)" % sorted(failed)[:3]
    if kind == "nonce":
        return "passed every hand trail, caught by the nonce population" \
            if nonce and not hand else \
            "caught by %d hand trails, not the forgery it should be" % len(hand)
    return "caught (%s)" % (sorted(failed)[:2] or "no test ran")


def main():
    pick = sys.argv[1] if len(sys.argv) > 1 else ""
    bad = []
    for script in sorted((lab.TASK / "cheat").glob("cheat-*.sh")):
        name = script.name[len("cheat-"):-len(".sh")]
        if pick and pick not in name:
            continue
        reward, failed, hand, timed, nonce, blank, _text = one(script)
        say = verdict(name, reward, failed, hand, timed, nonce, blank)
        ok = reward == 0 and not say.startswith("NOT")
        if not ok:
            bad.append(name)
        print("%-26s reward=%d  %s" % (name, reward, say), flush=True)
    print("\n%s" % ("every cheat scored 0 and was caught by the layer it should be"
                    if not bad else "PROBLEM: %s" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
