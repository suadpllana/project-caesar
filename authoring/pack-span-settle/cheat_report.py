"""Which layer catches each cheat, not just what it scored.

A reward of 0 proves nothing about why. A wrong reading has to be caught by the enumerated case
named for it, so a failure names the rule instead of "six of three hundred generated shards
wrong". A forgery has to be caught by the population it could not have seen, which means first
proving it really does reproduce the shards it was given - a forgery that quietly stopped
working scores 0 for the wrong reason. A slow family has to be caught by the clock, which means
proving it is exactly correct everywhere it finishes.

The probes are not measured here: they attack the verifier rather than the contract, and the
only thing that proves they are stopped is a real trial. `host_trial.py --all` runs those.

    python3 authoring/pack-span-settle/cheat_report.py
"""
import pathlib
import sys
import tempfile
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import emit_extra  # noqa: E402
import lab  # noqa: E402

sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "seal"))
import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402

# The enumerated case each wrong reading must be caught by. A reading caught only by some other
# case is a reading whose rule has no case of its own, whatever readingcheck's first hit says.
NAMED = {
    "div-length": "carry-two",
    "div-first-step": "many-bands",
    "div-all-steps": "drop-part",
    "scored-length": "carry-two",
    "pay-at-piece": "band-waits",
    "step-at-shut": "band-waits",
    "step-before-lay": "band-waits",
    "cut-brim": "stranded-tail",
    "cut-floor-one": "room-one",
    "cut-always-back": "fill-brim",
    "first-at-op": "first-window",
    "lay-one-token": "one-token",
    "skip-two-token": "two-token",
    "skip-room": "one-token",
    "floor-strict": "floor-edge",
    "width-now": "width-next",
    "span-now": "span-next",
    "floor-now": "floor-next",
    "cross-score": "cross-count",
    "drop-late": "drop-part",
    "void-zero": "drop-void",
    "frac-raw": "frac-reduce",
    "sum-positions": "frac-sum",
}

WALL = 60


def overlay(files):
    room = pathlib.Path(tempfile.mkdtemp(prefix="pss-cheat-"))
    for name, src in files.items():
        (room / name).write_text(src, encoding="utf-8", newline="\n")
    return room


def run(here, lines, timeout=WALL):
    room = pathlib.Path(tempfile.mkdtemp(prefix="pss-shard-"))
    shard = room / "s.txt"
    shard.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    try:
        return lab.run(here, shard, timeout=timeout)
    except Exception as exc:
        return ["RAISED", type(exc).__name__]


def main():
    for build in emit.READINGS:
        build()
    emit_extra.slow_positions()
    emit_extra.slow_steps()
    emit_extra.forge_truth()

    bad = 0
    print("== wrong readings: caught by the case named for the rule")
    for name in sorted(NAMED):
        case = NAMED[name]
        here = lab.tree(overlay(emit.BUILT[name]))
        got = run(here, cases.ops(case))
        want = model.expect(cases.ops(case))
        ok = got != want
        print("   %-18s %-14s %s" % (name, case, "caught" if ok else "NOT CAUGHT"))
        if not ok:
            bad += 1

    print("== the forgery: reproduces what it was given, and nothing else")
    here = lab.tree(overlay(emit.BUILT["forge-truth"])) 
    kept = sum(1 for n in cases.ORDER if run(here, cases.ops(n)) == model.expect(cases.ops(n)))
    print("   reproduces %d of %d enumerated shards" % (kept, len(cases.ORDER)))
    if kept != len(cases.ORDER):
        print("   NOT A FORGERY any more: it no longer answers the shards it carries")
        bad += 1
    unseen = gen.one("edge", "forge-check")
    if run(here, unseen) == model.expect(unseen):
        print("   NOT CAUGHT: it answered a shard it could not have seen")
        bad += 1
    else:
        print("   produces the wrong trace on a generated shard")

    print("== the slow families: exactly correct, and over the clock")
    for name, shard, many in (("slow-positions", "deep", 1), ("slow-steps", "wide", 3)):
        here = lab.tree(overlay(emit.BUILT[name]))
        wrong = 0
        for case in cases.ORDER:
            if run(here, cases.ops(case)) != model.expect(cases.ops(case)):
                wrong += 1
        start = time.time()
        for i in range(many):
            big = gen.one(shard, "slow-check/%d" % i)
            got = run(here, big, timeout=WALL * 8)
            if got[:1] == ["RAISED"]:
                break
        took = time.time() - start
        over = took > WALL or got[:1] == ["RAISED"]
        print("   %-15s %d of %d enumerated wrong, %d %s shard(s) in %.1f s against a %d s clock "
              "on the whole set: %s"
              % (name, wrong, len(cases.ORDER), many, shard, took, WALL,
                 "over" if over else "INSIDE THE CLOCK"))
        if wrong or not over:
            bad += 1

    print("%s" % ("every cheat is caught by the layer it should be" if not bad
                  else "%d findings" % bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
