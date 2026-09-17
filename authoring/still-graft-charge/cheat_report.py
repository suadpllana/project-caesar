"""Which layer catches each cheat, not just that the reward came out 0.

A reward of 0 proves nothing on its own: a cheat can score 0 because its patch never applied,
because it crashed on the first program, or because the layer it was written to test never ran.
This runs every wrong reading over the enumerated set and the generated families and names the
first program that catches it, times the three unaffordable-but-correct families against the
stated limit, and checks that the forgery reproduces every enumerated program and then fails on
programs it could not have seen. The isolation probes are graded by the trial, not here, and
are listed as such.

    python3 authoring/still-graft-charge/cheat_report.py [per]
"""
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "still-graft-charge"
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))

import cases  # noqa: E402
import gen  # noqa: E402
import model  # noqa: E402
import readings  # noqa: E402
from fuzz import lay, under  # noqa: E402
from timings import under as bounded  # noqa: E402

LIMIT = 60
CAP = 180
SLOW = ("slow-copy", "slow-scan", "slow-plain")
PROBES = ("probe-answer-key", "probe-privilege", "probe-late-reward", "probe-plant-report",
          "probe-crash-worker", "probe-malformed", "probe-shrink-set", "probe-hijack-worker",
          "probe-rewrite-frozen")


def policy(files):
    """The reference with one reading's files swapped in, laid into a runnable tree."""
    import shutil
    import tempfile
    room = Path(tempfile.mkdtemp(prefix="report-"))
    for one in Path(readings.REFERENCE).glob("*.py"):
        shutil.copyfile(one, room / one.name)
    for name, src in files.items():
        (room / name).write_text(src, encoding="utf-8")
    return room


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 6
    enumerated = [(name, cases.ops(name)) for name in cases.ORDER]
    generated = [(name, lines) for fam, name, lines in gen.programs("report", per)
                 if fam not in ("wide", "deep")]
    truth = {name: model.expect(lines) for name, lines in enumerated}

    bad = 0
    print("== wrong readings: the first graded program that catches each")
    for name, files in sorted(readings.READINGS.items()):
        tree = lay(policy(files))
        hit = None
        where = "enumerated"
        got = under(tree, [lines for _n, lines in enumerated])
        for (case, lines), out in zip(enumerated, got):
            if out != truth[case]:
                hit = case
                break
        if hit is None:
            where = "generated"
            got = under(tree, [lines for _n, lines in generated])
            for (case, lines), out in zip(generated, got):
                if out != model.expect(lines):
                    hit = case
                    break
        if hit is None:
            bad += 1
            print("   NOT CAUGHT  %-16s nothing separates it" % name)
        else:
            print("   caught      %-16s by the %s program %s" % (name, where, hit))

    print("== correct and unaffordable: measured against the %d second limit" % LIMIT)
    print("   a structure has to be killed by one family, not by both")
    for stem in ([] if "--quick" in sys.argv else SLOW):
        tree = lay(HERE / "variants" / stem)
        killed = False
        for fam in ("wide", "deep"):
            lines = gen.one(fam, "report/%s" % fam)
            got, spent = bounded(tree, [lines], CAP)
            if got is None:
                killed = True
                print("   %-11s %-5s did not finish inside %ds, against a %ds limit"
                      % (stem, fam, CAP, LIMIT))
                continue
            same = got[0][0] == len(model.expect(lines))
            if spent > LIMIT:
                killed = True
            print("   %-11s %-5s %7.1fs  trace length %s  %s"
                  % (stem, fam, spent, "right" if same else "WRONG",
                     "over the limit" if spent > LIMIT else "inside the limit"))
            if not same:
                bad += 1
        if not killed:
            bad += 1
            print("   NOT KILLED  %s fits the limit on every family" % stem)

    print("== the forgery: what it reproduces, and where it stops")
    frozen = json.loads((TASK / "tests" / "seal" / "gt.json").read_text(encoding="utf-8"))
    forge = lay(forge_dir())
    got = under(forge, [lines for _n, lines in enumerated])
    kept = sum(1 for (name, _l), out in zip(enumerated, got) if out == frozen[name])
    print("   reproduces %d of %d enumerated programs" % (kept, len(enumerated)))
    if kept != len(enumerated):
        bad += 1
    got = under(forge, [lines for _n, lines in generated])
    missed = sum(1 for (name, lines), out in zip(generated, got)
                 if out != model.expect(lines))
    print("   wrong on %d of %d programs it could not have seen" % (missed, len(generated)))
    # A handful of unseen programs can come out right by accident: with nothing to replay the
    # forgery answers every charge with 0, and a program whose lines all share everything is
    # charged 0 anyway. What has to hold is that it cannot survive the population.
    if missed < 0.9 * len(generated):
        bad += 1

    print("== isolation probes, graded by the trial rather than here")
    for stem in PROBES:
        path = TASK / "cheat" / ("cheat-%s.sh" % stem)
        print("   %-22s %s" % (stem, "present" if path.is_file() else "MISSING"))
        if not path.is_file():
            bad += 1

    print("%d finding(s)" % bad)
    return 1 if bad else 0


def forge_dir():
    """The forgery's six files, pulled back out of the cheat script that carries them."""
    import tempfile
    text = (TASK / "cheat" / "cheat-forge-from-truth.sh").read_text(encoding="utf-8")
    room = Path(tempfile.mkdtemp(prefix="forge-"))
    part = None
    body = []
    for line in text.splitlines():
        if line.startswith("cat > /app/led/"):
            part = line.split("/app/led/")[1].split()[0]
            body = []
        elif line == "PYEOF" and part:
            (room / part).write_text("\n".join(body) + "\n", encoding="utf-8")
            part = None
        elif part:
            body.append(line)
    return room


if __name__ == "__main__":
    sys.exit(main())
