"""Every cheat scores 0 - and the layer named for it is the layer that stops it.

A sweep that reads only the reward reports a clean row for a cheat that was never installed,
or for one caught by something unrelated. So each cheat declares what must catch it: a
wrong reading names the hand case written for it, which must be among the sessions it gets
wrong; a forgery or isolation probe names the test that must fail; the three probes that
turn on a second uid, a root-owned reward channel or /proc reaping are left to
host_trial.py, which runs tests/test.sh verbatim, and to the two-container trial.

Everything runs through trial.py: the real runner over the real plan, the real grader.

    python authoring/repair-orderbook-engine/cheat_report.py [--small N] [--deep N]
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

# reading -> the hand case written for it; probe -> the test that must fail; "host" ->
# needs the privilege drop, judged by host_trial.py and the container trial.
#
# The plant, read and sweep probes are caught here by the session comparison, because the
# runner writes its own report after the run and the shipped engine behind the probe is
# wrong; what the probe was reaching for (a root-owned report descriptor, the sealed gt.json,
# a process that outlives the run) only exists under test.sh, where host_trial.py runs them
# and they still score 0. plant-and-crash exits the run early, so its planted report is
# missing every session it never reached.
EXPECT = {
    "avail-full": "show-interleaves",
    "keep-front": "show-goes-to-the-back",
    "band-skips": "band-does-not-look-past",
    "band-fixed": "band-steps-with-the-fills",
    "trip-after-walk": "trip-before-disclosure",
    "whole-band-fixed": "whole-counts-the-step",
    "whole-no-undo": "whole-leaves-nothing-behind",
    "whole-ignores-hand": "whole-discounts-the-same-hand",
    "whole-ignores-band": "whole-discounts-past-the-band",
    "whole-as-day": "whole-never-rests",
    "trip-by-price": "trip-order-is-arrival",
    "trip-at-park": "trip-waits-for-a-fill",
    "self-trade": "hand-pulled-at-the-front",
    "capacity-only": "fill-capacity-is-consumed",
    "child-before-disclosure": "fill-discloses-before-child-execution",
    "forget-trigger-rollback": "fill-rollback-restores-trigger-arrival",
    "inner-frame-only": "fill-parent-failure-discards-child-success",
    "last-fill-batch": "fill-descendants-before-siblings",
    "answer-key": "test_generated_sessions",
    "forge-rows": "test_ordinary_sessions",
    "forge-into-sink": "test_ordinary_sessions",
    "rebind-emit": "test_functions_untouched",
    "rewrite-engine": "test_tree_untouched",
    "bad-report": "test_the_run_completed",
    "fail-after-report": "test_worker_exited_cleanly",
    "plant-report": "test_ordinary_sessions",
    "plant-and-crash": "test_the_run_completed",
    "read-answers": "test_ordinary_sessions",
    "sweep-environment": "test_ordinary_sessions",
    "kill-monitor": "test_instrumentation_intact",
    "reward-daemon": "host",
    "probe-privileges": "host",
}


def wrong_sessions(report, plan, want):
    reports = report.get("reports", {})
    errors = report.get("errors", {})
    out = []
    for name in plan:
        got = reports.get(name, {}).get("ev")
        if name in errors or got != want[name]:
            out.append(name)
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--small", type=int, default=300)
    ap.add_argument("--deep", type=int, default=4)
    ap.add_argument("--only", default=None)
    args = ap.parse_args(argv[1:])
    nonce = "cheat-report"
    plan = dict(runner.plan(nonce, args.small, args.deep))
    want = {n: [list(r) for r in oracle.solve(t)] for n, t in plan.items()}
    rows, bad = [], 0
    for sh in sorted((TASK / "cheat").glob("cheat-*.sh")):
        name = sh.stem[len("cheat-"):]
        if args.only and name != args.only:
            continue
        expect = EXPECT.get(name)
        if expect is None:
            rows.append("   %-26s NO EXPECTATION - add it to EXPECT" % name)
            bad += 1
            continue
        if expect == "host":
            rows.append("   %-26s left to host_trial.py and the container trial (privilege drop)" % name)
            continue
        r = trial.run(sh, args.small, args.deep, nonce=nonce)
        if r["reward"] != 0:
            rows.append("   %-26s SCORED 1 - verifier defect" % name)
            bad += 1
            continue
        if expect.startswith("test_"):
            ok = expect in r["failed"]
            rows.append("   %-26s %s <- %s" % (name, "caught" if ok else "NOT CAUGHT BY " + expect,
                                              ", ".join(r["failed"])[:90] or "nothing failed"))
        else:
            wrong = wrong_sessions(r["report"], plan, want)
            hand = [n for n in wrong if n in cases.SESS]
            gen_wrong = len(wrong) - len(hand)
            ok = expect in hand
            rows.append("   %-26s %s by %s; %d hand, %d generated sessions wrong" % (
                name, "named" if ok else "NOT NAMED", expect, len(hand), gen_wrong))
        if not ok:
            bad += 1
        print(rows[-1], flush=True)
    print("== repair-orderbook-engine cheat layers")
    for r in rows:
        print(r)
    print("   %d of %d cheats caught by the layer named for them" % (len(rows) - bad, len(rows)))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
