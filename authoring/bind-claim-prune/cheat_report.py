"""Every cheat, with the layer that caught it - not only the number it scored.

A zero is not evidence on its own. A probe whose payload threw before it did anything, a
forgery that never reproduced a single answer, a wrong reading whose patch matched nothing: all
of them score 0, and all of them mean the check they were written for did not happen. So this
records which tests failed for each cheat, what the probe wrote down about what it was refused,
and holds both against what the cheat was written to trip.

The forgery carries the extra expectation that says whether it is a forgery at all: it has to
pass every enumerated program and fail only the ones it could not have seen. A forgery that
fails the enumerated programs too is just another broken engine.

    python authoring/bind-claim-prune/cheat_report.py [<name fragment>]
"""
import fcntl
import os
import pathlib
import re
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import host_trial as ht  # noqa: E402

TASK = ht.TASK
CHEATS = TASK / "cheat"

# layers: what the cheat has to trip. clean: layers it must NOT trip. note: text the probe has
# to have written down. A name is an enumerated case; `nonce` is the generated population;
# `worker` means the worker stage itself came back non-zero.
WANT = {
    "cheat-at-preprune.sh": {"layers": ("prune-drop",)},
    "cheat-claim-never.sh": {"layers": ("claim-drop",)},
    "cheat-claim-sticks.sh": {"layers": ("shift-key",)},
    "cheat-dup-replaces.sh": {"layers": ("dup-report",)},
    "cheat-firm-never.sh": {"layers": ("shift-firm",)},
    "cheat-give-stays.sh": {"layers": ("shift-key",)},
    "cheat-group-once.sh": {"layers": ("group-pass",)},
    "cheat-hold-quiet.sh": {"layers": ("prune-hold",)},
    "cheat-img-all-spares.sh": {"layers": ("spare-reach",)},
    "cheat-one-give.sh": {"layers": ("shift-rebind",)},
    "cheat-rescan-back.sh": {"layers": ("shift-earlier",)},
    "cheat-spare-first.sh": {"layers": ("spare-size",)},
    "cheat-spare-late.sh": {"layers": ("spare-size",)},
    "cheat-spare-quiet.sh": {"layers": ("spare-want",)},
    "cheat-take-oldest.sh": {"layers": ("take-order",)},
    "cheat-take-onward.sh": {"layers": ("take-restart",)},
    "cheat-use-stays.sh": {"layers": ("shift-use-gone",)},
    "cheat-weak-reaches.sh": {"layers": ("weak-reach",)},
    "cheat-weak-settles.sh": {"layers": ("weak-give",)},
    "cheat-weak-wants.sh": {"layers": ("weak-use-quiet",)},

    "cheat-list-as-group.sh": {"layers": ("group-none",)},
    "cheat-take-again.sh": {"layers": ("take-loaded",)},

    "cheat-slow-rescan.sh": {"layers": ("worker",)},
    "cheat-slow-rebuild.sh": {"layers": ("worker",)},
    "cheat-slow-perpart.sh": {"layers": ("worker",)},

    # it has to pass every program it was handed the answer to, and fail the rest
    "cheat-forge-answers.sh": {"layers": ("nonce",), "clean": "hand"},

    "cheat-probe-answer-key.sh": {"layers": ("nonce",), "unnote": "model imported from"},
    "cheat-probe-late-reward.sh": {"layers": ("nonce",)},
    "cheat-probe-plant-report.sh": {"layers": ("nonce",), "unnote": "report planted"},
    "cheat-probe-crash-worker.sh": {"layers": ("hand",), "note": "planted then exiting clean"},
    "cheat-probe-malformed.sh": {"layers": ("hand",), "note": "garbage written"},
    "cheat-probe-privilege.sh": {"layers": ("nonce",),
                                 "note": "refused /logs/verifier/reward.txt"},
    "cheat-probe-shrink-set.sh": {"layers": ("nonce",), "note": "refused /logs/verifier/per"},
    "cheat-probe-hijack-driver.sh": {"layers": ("nonce",),
                                     "note": "refused /tests/test_outputs.py"},
    "cheat-probe-rewrite-frozen.sh": {"layers": ("nonce",)},
}

CASE = re.compile(r"test_hand_case\[([^\]]+)\]")


def run(cheat):
    art = ht.agent_stage(cheat, False)
    reward, proc = ht.verifier_stage(art)
    text = proc.stdout + proc.stderr
    cases = sorted(set(CASE.findall(text)))
    layers = set(cases)
    if cases:
        layers.add("hand")
    if "test_every_nonce_program_matches" in text or "test_every_family_is_represented" in text:
        layers.add("nonce")
    worker = re.search(r"worker exit (\d+)", text)
    if worker and worker.group(1) != "0":
        layers.add("worker")
    log = ht.WORK / "probe.log"
    note = log.read_text(encoding="utf-8") if log.is_file() else ""
    return reward, cases, layers, note


def main():
    # This drives the same fixed /app, /tests, /work and /logs that host_trial.py does, so a
    # second copy running beside it reads the other's tree and reports rows that belong to
    # neither. forgecheck.py runs this file itself, which is exactly how that happened.
    fd = os.open(str(ht.LOCK), os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError:
        raise SystemExit("another trial is running (%s)" % ht.LOCK)
    pick = sys.argv[1] if len(sys.argv) > 1 else ""
    rows = []
    bad = 0
    for cheat in sorted(CHEATS.glob("*.sh")):
        if pick and pick not in cheat.name:
            continue
        reward, cases, layers, note = run(cheat)
        need = WANT.get(cheat.name)
        why = []
        if reward != 0:
            why.append("SCORED 1")
        if need is None:
            why.append("no expectation recorded")
        else:
            for want in need.get("layers", ()):
                if want not in layers:
                    why.append("did not trip %s" % want)
            if need.get("clean") and need["clean"] in layers:
                why.append("tripped %s, which it was supposed to reproduce" % need["clean"])
            if need.get("note") and need["note"] not in note:
                why.append("probe never wrote %r" % need["note"])
            if need.get("unnote") and need["unnote"] in note:
                why.append("probe reported %r - the attack was not refused" % need["unnote"])
        if why:
            bad += 1
        rows.append((cheat.name, reward, sorted(layers), "; ".join(why),
                     " | ".join(note.split("\n"))[:150]))
    print("%-34s %6s  %s" % ("cheat", "reward", "layers that caught it"))
    for name, reward, layers, why, note in rows:
        print("%-34s %6d  %s" % (name, reward, ", ".join(layers[:5]) or "NOTHING"))
        if why:
            print("     FINDING: %s" % why)
        if note:
            print("     probe: %s" % note)
    print("\n%d cheats, %d findings" % (len(rows), bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
