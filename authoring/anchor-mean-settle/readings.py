"""Grade every wrong reading against the hand cases and the generated population.

Run as a script it reports, for each reading, the enumerated case named for that rule and
whether that case is what fails it, plus the share of a shaped population the reading moves.
A reading that moves nothing is a reading the population is not shaped for; with
all-or-nothing grading a reading that moves one program in a hundred still scores 0, but a
reading no case names is a rule nothing is proving.

Imported, it is also the contract `tools/readingcheck.py` reads - REFERENCE, READINGS, run,
enumerated, generated - so the two tools cannot disagree about what a reading is or which
case separates it.

    python3 authoring/anchor-mean-settle/readings.py [per-family]
    python3 tools/readingcheck.py anchor-mean-settle 40
"""
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / "tasks" / "anchor-mean-settle" / "tests"))

import cases  # noqa: E402
import gen  # noqa: E402
import probe  # noqa: E402

sys.path.insert(0, str(HERE / "lab"))
import tree as model  # noqa: E402

TASK = HERE.parent.parent / "tasks" / "anchor-mean-settle"
REFERENCE = str(TASK / "solution")
PARTS = ("grid.py", "gues.py", "seat.py", "step.py", "edit.py", "ask.py")


def _readings():
    """{name: {filename: source}} for the files each reading actually replaces."""
    out = {}
    for d in sorted((HERE / "readings").iterdir()):
        if not d.is_dir():
            continue
        files = {}
        for part in PARTS:
            src = (d / part).read_text(encoding="utf-8")
            if src != (TASK / "solution" / part).read_text(encoding="utf-8"):
                files[part] = src
        out[d.name] = files
    return out


READINGS = _readings()

_SEEN = {}


def run(policy, text):
    """One program under one set of the six modules, as a comparable trace."""
    key = (str(policy), text)
    got = _SEEN.get(key)
    if got is None:
        out, err = probe.run(str(policy), [("p", text.split("\n"))])
        if out is None:
            raise RuntimeError(err)
        got = tuple(out["p"])
        _SEEN[key] = got
    return got


def enumerated():
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    out = []
    per = max(1, n // 10 + 1)
    for fam, name, lines in gen.programs("readingcheck", per):
        if fam in ("wide", "deep"):
            continue
        out.append((name, "\n".join(lines)))
        if len(out) >= n:
            break
    return out

# The case each reading has to fail. Scoring 0 is not the claim - the claim is that the
# enumerated case named for a rule is what proves that rule, so a reading of it fails by
# name rather than by luck somewhere in the population.
NAMED = {
    "est-default": "mean-one",
    "est-all-rows": "mean-one",
    "est-round-up": "mean-floor",
    "pass-one-step": "pass-grow",
    "pass-seat-last": "pass-grow",
    "pass-highest": "pass-grow",
    "pass-anchor-last": "anchor-first",
    "pass-redo-dy": "clamp-hold",
    "seat-no-clamp": "clamp-shrink",
    "roll-no-clamp": "roll-past",
    "roll-keep-anchor": "roll-past",
    "edit-no-seat": "ins-above",
    "del-drop-anchor": "del-anchor",
    "del-fall-back": "del-anchor",
    "del-no-tail": "del-tail",
    "move-fresh": "move-keep",
    "move-falls-off": "move-anchor",
    "set-keeps-height": "set-drop",
    "span-keeps-all": "span-all",
    "tall-measured-only": "tall-mixed",
    "face-row-after": "face-inside",
    "face-absolute": "face-inside",
    "hit-row-at-or-after": "face-inside",
    "stale-offsets": "mean-above",
}


def population(PER):
    jobs = [("hand:" + n, cases.ops(n)) for n in cases.ORDER]
    for fam, name, lines in gen.programs("readings-seed", PER):
        if fam in ("wide", "deep"):
            continue
        jobs.append(("%s:%s" % (fam, name), lines))
    return jobs


def main():
    PER = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    jobs = population(PER)
    want = {n: model.run(l) for n, l in jobs}
    hands = [n for n, _ in jobs if n.startswith("hand:")]

    ref = probe.run(REFERENCE, jobs)[0]
    off = [n for n in want if ref.get(n) != want[n]]
    print("reference against the model: %d of %d differ %s" % (len(off), len(jobs), off[:3]))

    rows = []
    for d in sorted((HERE / "readings").iterdir()):
        if not d.is_dir():
            continue
        got, err = probe.run(str(d), jobs)
        if got is None:
            rows.append((d.name, "-", 0, "crashed: %s" % err))
            continue
        wrong = [n for n in want if got.get(n) != want[n]]
        named = NAMED.get(d.name)
        ok = named is not None and got.get("hand:" + named) != want.get("hand:" + named)
        if named is None:
            tag = "UNMAPPED"
        elif ok:
            tag = named
        else:
            tag = "%s NOT CAUGHT" % named
        pop = [n for n in wrong if not n.startswith("hand:")]
        rows.append((d.name, tag, len(pop), "%d/%d" % (len(wrong), len(jobs))))

    print()
    print("%-22s %-24s %6s  %s" % ("reading", "case named for the rule", "pop", "moved"))
    for name, caught, pop, moved in rows:
        bad = "NOT CAUGHT" in caught or caught == "UNMAPPED"
        print("%-22s %-24s %6d  %s%s" % (name, caught, pop, moved,
                                         "   <--" if bad else ""))
    loose = [r[0] for r in rows if "NOT CAUGHT" in r[1] or r[1] == "UNMAPPED"]
    print()
    print("%d readings, %d failed by the case named for their rule" % (len(rows), len(rows) - len(loose)))
    if loose:
        print("not proven by name:", loose)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
