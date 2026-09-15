"""Turn every reading and probe directory into a cheat script.

Runs after make_readings.py and make_probes.py, never before: a cheat emitted from a stale
directory tests the reading as it used to be, and two tools disagreeing about what a cheat
contains is exactly how that goes unnoticed.
"""
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TASK = HERE.parents[1] / "tasks" / "blend-roll-resume"
CHEAT = TASK / "cheat"
PARTS = ("deck.py", "pick.py", "walk.py", "lay.py", "keep.py", "turn.py")

sys.path.insert(0, str(HERE))

HEAD = "#!/bin/bash\nset -euo pipefail\n\n"

# Cheats that do something the six files cannot express on their own.
EXTRA = {
    "probe-hijack-driver": (
        "cat > /app/ops.py <<'PYEOF'\n"
        "from mix import deck, keep, turn\n"
        "\n"
        "\n"
        "def ex(h, p):\n"
        "    if p[0] == 'feed':\n"
        "        h.out.append('feed %s %s ab:5 ab:11' % (p[1], p[2]))\n"
        "    elif p[0] == 'at':\n"
        "        h.out.append('at %s 0 0' % p[1])\n"
        "PYEOF\n"
        "cat > /app/mix/perm.py <<'PYEOF'\n"
        "def order(seed, idx, epoch, n):\n"
        "    return list(range(n))\n"
        "PYEOF\n"),
}

WHY = {
    "at-departed": "a departed source still reports an epoch and a cursor",
    "cap-early": "a capped source leaves as its last permitted epoch begins",
    "cap-late": "a capped source serves one epoch past its cap",
    "depart-step-end": "a departure takes effect when the step it fell in is over",
    "done-next-draw": "a done line carries the draw after the one that took the last sample",
    "feed-announces": "a feed announces a departure it only looked at",
    "feed-commits": "a feed takes the draws it reports",
    "feed-own-slot": "a feed settles only its own micro-batch",
    "join-reset": "a stop puts back every source, the ones it never saw included",
    "keep-blend": "a stop puts the blend back along with the run",
    "lay-contig": "each rank takes one contiguous block of the step",
    "lay-no-accum": "the accumulation depth does not widen a step",
    "no-rebase-drop": "a departure leaves the remaining counters where they are",
    "no-rebase-join": "declaring a source mid-run leaves the counters where they are",
    "no-rebase-weigh": "a reweighing leaves the counters where they are",
    "rebase-always": "a restart always starts a fresh segment",
    "rebase-by-sum": "the blend counts as unchanged while the live count and weight total hold",
    "rebase-never": "the counters a stop puts back always stand",
    "slow-per-draw": "exactly correct, and reaches a queried step by taking every draw",
    "slow-per-step": "exactly correct, and settles the counters once per step of the run",
    "tie-late": "a tie in the draw rule goes to the later declared source",
    "tie-weight": "a tie in the draw rule goes to the heavier source",
    "total-counter": "the draw rule reads whole consumption, not draws since the blend changed",
    "shortcut-const": "one fixed micro-batch for every question and no departures at all",
    "shortcut-first-source": "every draw goes to the first live source",
    "shortcut-example": "the line the brief publishes, replayed for every question",
    "forge-from-truth": "the frozen answer for every enumerated script, carried and replayed",
    "probe-answer-key": "reads the sealed answers from inside the graded run",
    "probe-plant-report": "plants the worker's report before the run writes it",
    "probe-exit-clean": "plants a passing report and leaves cleanly before it is overwritten",
    "probe-late-reward": "double-forks a survivor that writes the reward after grading",
    "probe-malformed": "hands the grader output of the wrong shape",
    "probe-privilege": "checks its uid and writes at the verifier's own files",
    "probe-shrink-set": "rewrites the seed and the count so fewer scripts are generated",
    "probe-kill-grader": "empties the grader's files and signals the process that started it",
    "probe-hijack-driver": "rewrites the files the verifier does not take from the agent",
}


def emit(room):
    name = room.name
    body = [HEAD, "# %s\n\n" % WHY.get(name, name)]
    for part in PARTS:
        one = room / part
        if not one.is_file():
            continue
        body.append("cat > /app/mix/%s <<'PYEOF'\n" % part)
        body.append(one.read_text(encoding="utf-8").rstrip("\n") + "\n")
        body.append("PYEOF\n\n")
    body.append(EXTRA.get(name, ""))
    text = "".join(body)
    assert "\r" not in text
    (CHEAT / ("cheat-%s.sh" % name)).write_text(text, encoding="utf-8", newline="\n")


def main():
    shutil.rmtree(CHEAT, ignore_errors=True)
    CHEAT.mkdir(parents=True)
    rooms = []
    for base in ("readings", "probes"):
        rooms += [d for d in sorted((HERE / base).iterdir()) if d.is_dir()]
    missing = [d.name for d in rooms if d.name not in WHY]
    if missing:
        print("no description for: %s" % ", ".join(missing))
        return 1
    for room in rooms:
        emit(room)
    print("wrote %d cheats" % len(rooms))
    return 0


if __name__ == "__main__":
    sys.exit(main())
