"""Score the degenerate strategies of docs/INSTRUCTION-CONTRACT.md, each as a submission.

Reward is all-or-nothing, so the number that matters is the second one: how many of the
graded sessions a strategy that does no work gets exactly right. A strategy matching most
sessions would say the population barely exercises the rules; these should match almost
none. Each row is a real submission through trial.py - the shipped tree (nop), an engine
that never trades (`shortcuts/silent`: every walk fills nothing, every whole is refused,
nothing ever fires), the previous reference that predates fill pace (the cheat
`capacity-only`), an all-or-nothing order treated as an ordinary resting order (the cheat
`whole-as-day`, the positional strategy of resting whatever is left), and the whole ground
truth replayed (the cheat `answer-key`).

    python authoring/repair-orderbook-engine/shortcuts.py [--small N] [--deep N]
"""
import argparse
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "repair-orderbook-engine"
HERE = ROOT / "authoring" / "repair-orderbook-engine"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(HERE))

import cases  # noqa: E402
import oracle  # noqa: E402
import runner  # noqa: E402
import trial  # noqa: E402

STRATEGIES = [
    ("the shipped tree unchanged (nop)", None),
    ("constant: an engine that never trades, fires or admits", HERE / "shortcuts" / "silent"),
    ("the previous reference, from before fill pace (capacity-only)",
     TASK / "cheat" / "cheat-capacity-only.sh"),
    ("positional: rest whatever a whole order could not fill (whole-as-day)",
     TASK / "cheat" / "cheat-whole-as-day.sh"),
    ("the worked truth replayed: gt.json carried whole (answer-key)",
     TASK / "cheat" / "cheat-answer-key.sh"),
]


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--small", type=int, default=300)
    ap.add_argument("--deep", type=int, default=4)
    args = ap.parse_args(argv[1:])
    nonce = "shortcuts"
    plan = dict(runner.plan(nonce, args.small, args.deep))
    want = {n: [list(r) for r in oracle.solve(t)] for n, t in plan.items()}
    hand = [n for n in plan if n in cases.SESS]
    print("== repair-orderbook-engine shortcut strategies, %d sessions (%d hand)"
          % (len(plan), len(hand)))
    worst = 0
    for label, source in STRATEGIES:
        r = trial.run(source, args.small, args.deep, nonce=nonce)
        reports = r["report"].get("reports", {})
        errors = r["report"].get("errors", {})
        right = [n for n in plan if n not in errors and reports.get(n, {}).get("ev") == want[n]]
        right_hand = [n for n in right if n in cases.SESS]
        print("   reward %d  %3d/%d sessions exact (%d/%d hand)   %s"
              % (r["reward"], len(right), len(plan), len(right_hand), len(hand), label),
              flush=True)
        worst = max(worst, r["reward"])
    return 1 if worst else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
