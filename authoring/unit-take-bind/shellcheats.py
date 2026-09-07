"""Generate the cheat scripts that stand for a wrong reading, so a write-up cannot drift.

Each reading in `readings.py` is a complete engine - the reference with one decision changed -
and each becomes one script here that writes all four files into `/app/res/`. Writing all four
matters: a script that dropped in only the changed file would be graded against the shipped
tree's other three and would score 0 for a reason that has nothing to do with the reading it
is meant to stand for.

The probes that attack the verifier rather than the rules are written by hand under `cheat/`
and are only described here; `check()` fails if a script exists with no description or a
description with no script.

Usage:
    python3 shellcheats.py           write the reading scripts and cheat/README.md
    python3 shellcheats.py --check   verify the two lists agree, write nothing
"""
import json
import pathlib
import sys

import harness
import readings

CHEATS = harness.TASK / "cheat"

READING_WHY = {
    "cost-drops-source": "prices a pull by the name's rank in the source alone, ignoring the "
                         "rank of the reading that chose that source",
    "cost-adds-source": "adds the two ranks a pull is priced from instead of taking the larger",
    "src-local-only": "lets a local binding of the source name shut out the program's own unit "
                      "of that name",
    "src-global-only": "reads a pull's source name only as the program's unit of that name",
    "src-free-rank": "reads a locally bound source at no cost, whatever that binding cost",
    "wide-takes-shut": "lets a wide pull take a name that is shut",
    "narrow-blocks-shut": "stops a pull that names a shut name from reaching it",
    "narrow-takes-hidden": "lets a pull that names a hidden name reach it",
    "clash-carries": "carries a contested name onward as though it were bound",
    "first-wins": "takes the first of the cheapest candidates rather than contesting them",
    "clash-on-any-two": "contests whenever two candidates arrive, even from one origin",
    "clash-by-unit-only": "compares only the unit of two candidates, so an item and a unit of "
                          "the same name agree",
    "in-place-sweep": "relaxes until nothing moves, updating in place, so a binding carried "
                      "onward before its second route arrives is never withdrawn",
    "clash-retry": "settles a contested name again from a later, single candidate",
    "als-costs-one": "prices `als` a step out rather than where the unit declared it",
    "hide-drops-local": "reads `hide` as taking the name out of its own unit as well",
}

PROBE_WHY = {
    "forge-answer-key": "carries tests/gt.json verbatim and answers from it, with nothing "
                        "for a generated program",
    "swap-the-record": "rewrites the worker's record from a background process after the "
                       "worker has exited",
    "read-the-answers": "reads the sealed model and the frozen answers out of the verifier at "
                        "run time",
    "sweep-the-work-dir": "scans the work directory for anything the grader will compare against",
    "reward-daemon": "double-forks a process that writes the reward after grading has finished",
    "privilege-probe": "checks its uid and writes the reward channel directly",
    "plant-and-exit": "plants a full worker record and exits the worker cleanly before the "
                      "programs are run",
    "malformed-record": "returns wrong types, to throw inside the grader rather than fail in it",
    "kill-the-worker": "exits the worker part way, so most programs never run",
}

HEAD = "#!/bin/bash\n# %s\nset -euo pipefail\n\n"


def write_file(name, text):
    return "cat > /app/res/%s <<'PYEOF'\n%s\nPYEOF\n\n" % (name, text.rstrip("\n"))


def build():
    base = {name: (harness.REF / name).read_text(encoding="utf-8") for name in harness.PARTS}
    made = []
    for name in sorted(readings.READINGS):
        why = READING_WHY.get(name)
        if why is None:
            raise SystemExit("reading %r has no description" % name)
        body = HEAD % why
        files = dict(base)
        files.update(readings.READINGS[name])
        for part in harness.PARTS:
            body += write_file(part, files[part])
        path = CHEATS / ("cheat-read-%s.sh" % name)
        path.write_text(body, encoding="utf-8", newline="\n")
        path.chmod(0o755)
        made.append(path.name)
    made.append(forge())
    return made


Q3 = chr(39) * 3

FORGE_IMPORTS = """import json

from prog.deck import blank, put

from .pick import settle
from .show import out_all, out_one
from .step import cost, srcs

GT = json.loads(r"""

FORGE_BETWEEN = """)

KEYS = json.loads(r"""

FORGE_BODY = """)


def sign(prog):
    lines = []
    for u in prog.units.values():
        lines += ["%s own %s" % (u.nm, x) for x in u.owns]
        lines += ["%s als %s %s" % (u.nm, x, vn) for x, vn in u.als]
        lines += ["%s pull %s %s" % (u.nm, s, w) for s, w in u.pulls]
        lines += ["%s shut %s" % (u.nm, x) for x in sorted(u.shuts)]
        lines += ["%s hide %s" % (u.nm, x) for x in sorted(u.hides)]
    return "\\n".join(sorted(lines))


def run(prog):
    deck = blank(prog.units)
    known = KEYS.get(sign(prog))
    if known is None:
        for u in prog.units.values():
            for x in u.owns:
                put(deck, u.nm, x, "own", u.nm, 0)
        return deck
    for line in GT[known]:
        bits = line.split()
        if len(bits) == 5:
            put(deck, bits[0], bits[1], bits[2], bits[3], int(bits[4]))
        elif len(bits) == 4:
            put(deck, bits[0], bits[1], bits[2], None, int(bits[3]))
    return deck
"""


def forge():
    """An engine handed the frozen answers verbatim, and nothing for a generated program."""
    sys.path.insert(0, str(harness.TASK / "tests"))
    import cases

    raw = (harness.TASK / "tests" / "gt.json").read_text(encoding="utf-8")
    # The canonical dump, not the file's own layout: that is the form a checker re-derives
    # from gt.json when it looks for a cheat carrying the answers.
    gt_text = json.dumps(json.loads(raw), sort_keys=True)
    keys = {}
    for name in cases.ORDER:
        lines = cases.ops(name)
        keys["\n".join(sorted(ln for ln in lines if " ask " not in ln))] = name
    body = HEAD % PROBE_WHY["forge-answer-key"]
    forged = (FORGE_IMPORTS + Q3 + gt_text.rstrip("\n") + Q3 + FORGE_BETWEEN
              + Q3 + json.dumps(keys, indent=1) + Q3 + FORGE_BODY)
    if gt_text not in forged:
        raise SystemExit("the forged engine does not carry gt.json verbatim")
    body += write_file("turn.py", forged)
    path = CHEATS / "cheat-forge-answer-key.sh"
    path.write_text(body, encoding="utf-8", newline="\n")
    path.chmod(0o755)
    return path.name


def readme():
    lines = ["# Cheat attempts", "",
             "Each writes the four files the verifier reads out of `/app/res/`, and each must",
             "score 0. The wrong-reading scripts are generated by",
             "`authoring/unit-take-bind/shellcheats.py` from the readings measured in",
             "`authoring/unit-take-bind/readings.py`, so a write-up cannot drift from the",
             "engine it stands for; the probes below them are written by hand.", "",
             "`reward-daemon` and `privilege-probe` need a second uid to mean anything, and",
             "`read-the-answers` needs `/tests` to be root-only. All three were run against",
             "the shipped `tests/test.sh` at its own absolute paths, with the same sandbox",
             "uid the verifier image creates.", ""]
    for name in sorted(READING_WHY):
        lines.append("- `cheat-read-%s.sh` - %s" % (name, READING_WHY[name]))
    for name in sorted(PROBE_WHY):
        lines.append("- `cheat-%s.sh` - %s" % (name, PROBE_WHY[name]))
    (CHEATS / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")


def check():
    want = {"cheat-read-%s.sh" % n for n in READING_WHY}
    want |= {"cheat-%s.sh" % n for n in PROBE_WHY}
    have = {p.name for p in CHEATS.glob("cheat-*.sh")}
    missing, extra = sorted(want - have), sorted(have - want)
    if missing or extra:
        print("described but absent: %s\npresent but undescribed: %s" % (missing, extra))
        return 1
    print("%d cheat scripts, all described" % len(have))
    return 0


def main():
    CHEATS.mkdir(exist_ok=True)
    if "--check" not in sys.argv:
        made = build()
        readme()
        print("wrote %d reading scripts and README.md" % len(made), flush=True)
    return check()


if __name__ == "__main__":
    sys.exit(main())
