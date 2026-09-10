"""Run every cheat and record which layer caught it.

A reward of 0 is not the finding: a probe that fails for its own reasons, or a wrong reading
that only the generated population happens to catch, both score 0 and both mean the intended
guard was never exercised. So every cheat declares what should catch it - a named enumerated
case, the generated population, or the execution limit - and this fails when the layer does not
match.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "claim-raise-cut"
CHEATS = TASK / "cheat"

# What must catch each cheat: a hand case name, "nonce", or "limit". Four of the wrong
# readings are also slow enough to miss the limit on the two large families, so at full scale
# they never reach the comparison that names them; `small_scale.py` runs those four with the
# large families out and confirms the enumerated case. `probe-reward-later` reads as "limit"
# here for a reason that belongs to this harness rather than to the task - its double-forked
# child holds the pipe this script waits on - and the container trial shows it caught by the
# hand cases.
EXPECT = {
    "join-rank": "join-pair",
    "raise-ask-mark": ("join-pair", "limit"),
    "self-count": "self-alone",
    "raise-ask-order": "raise-order",
    "pin-none": "pin-fresh",
    "pin-bar": ("raise-pass", "limit"),
    "queue-skip": "queue-stop",
    "edge-conflict": ("edge-miss", "limit"),
    "edge-and": ("edge-phantom", "limit"),
    "cut-young": "cut-wake",
    "cut-early": "cut-late",
    "cut-most": "cut-fewest",
    "cut-one-ring": ("cut-again", "ring-pair"),
    "cut-once": "cut-again",
    "cut-no-cancel": "cut-wake",
    "cut-no-wake": "cut-wake",
    "drop-all": "drop-pop",
    "shed-name": "shed-order",
    "resume-now": "resume-order",
    "settle-block": "cut-again",
    "per-participant": "limit",
    "all-live": "limit",
    "whole-rebuild": "limit",
    "candidate-verify": "limit",
    "probe-answer-key": "join-pair",
    "probe-reward-now": "join-pair",
    "probe-reward-later": ("join-pair", "limit"),
    "probe-plant-exit": "nonce",
    "probe-malformed": "join-pair",
    "probe-privilege": "join-pair",
    "probe-shrink": "join-pair",
    "probe-hijack-tree": "join-pair",
    "probe-hang": "limit",
    "probe-forge-frozen": "nonce",
}


def run(script, out):
    got = subprocess.run(
        [sys.executable, "-u", str(HERE / "host_trial.py"),
         "--script", str(script), "--json", str(out)],
        capture_output=True, text=True, cwd=str(HERE.parent.parent))
    try:
        return json.loads(Path(out).read_text(encoding="utf-8")), got.stdout
    except Exception:
        return None, got.stdout + got.stderr


def layers(res):
    """Every layer that caught this cheat: the enumerated cases by name, plus `nonce` and
    `limit` where they apply. A cheat is judged on whether the layer it was written for is
    among them, not on whichever one pytest happened to report first."""
    if res is None:
        return ["no result"]
    out = []
    if res.get("over"):
        out.append("limit")
    for name in res.get("failed", []):
        if name.startswith("test_hand_case["):
            out.append(name.split("[", 1)[1].rstrip("]"))
        elif "nonce" in name:
            out.append("nonce")
        else:
            out.append(name)
    if not out and res.get("worker"):
        out.append("worker")
    return out or ["-"]


def main():
    only = sys.argv[1:] or None
    room = Path(tempfile.mkdtemp(prefix="crc-cheats-"))
    rows, bad = [], []
    for script in sorted(CHEATS.glob("cheat-*.sh")):
        name = script.name[len("cheat-"):-len(".sh")]
        if only and name not in only:
            continue
        res, log = run(script, room / (name + ".json"))
        got = layers(res)
        want = EXPECT.get(name, "?")
        wants = want if isinstance(want, tuple) else (want,)
        reward = -1 if res is None else res.get("reward", -1)
        rows.append((name, reward, got, want, res.get("took") if res else None))
        if reward != 0:
            bad.append("%s scored %s" % (name, reward))
        elif want == "?":
            bad.append("%s has no expected layer" % name)
        elif not any(w in got for w in wants):
            bad.append("%s was caught by %s, none of them %r" % (name, ", ".join(got[:4]), want))
        print("%-22s reward %-2s want %-13s caught by %2d: %s  %ss"
              % (name, reward, want, len(got), ", ".join(got[:3]), rows[-1][4]), flush=True)
    print()
    for line in bad:
        print("FINDING:", line)
    print("%d cheats, %d findings" % (len(rows), len(bad)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
