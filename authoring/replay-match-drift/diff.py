"""Reference against sealed model, over the generated population and the samples.

The two were written apart - the reference reads the log through dicts of lists and a
counter per axis, the model walks flat arrays indexed by log position - so agreement over a
large shaped population is what says the verifier grades the contract rather than one
implementation. Run it after any change to either side or to the generator.
"""
import pathlib
import shutil
import sys
import tempfile
import time

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "replay-match-drift"
PARTS = ("tab", "edge", "pair", "pend", "sigq", "ver")


def staged(which):
    room = pathlib.Path(tempfile.mkdtemp())
    shutil.copytree(TASK / "environment" / "app_src", room / "app")
    if which == "ref":
        for part in PARTS:
            shutil.copy(TASK / "solution" / (part + ".py"), room / "app" / "dur" / (part + ".py"))
    return room / "app"


def main():
    seeds = sys.argv[1:] or ["s1", "s2", "s3"]
    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "tests" / "seal"))
    import gen
    import model

    here = staged("ref")
    sys.path.insert(0, str(here))
    import run_dur

    work = []
    for name in sorted((TASK / "environment" / "app_src" / "runs").glob("*.txt")):
        work.append(("sample", name.name, name.read_text(encoding="utf-8").splitlines()))
    for seed in seeds:
        work.extend(gen.programs(seed, 12))

    bad = 0
    slow = []
    for fam, name, lines in work:
        start = time.time()
        got = run_dur.run("\n".join(lines) + "\n")
        spent = time.time() - start
        want = model.expect(lines)
        if spent > 1.0:
            slow.append((name, round(spent, 2)))
        if got != want:
            bad += 1
            if bad < 4:
                print("DIFFER %s/%s" % (fam, name))
                for i in range(max(len(got), len(want))):
                    g = got[i] if i < len(got) else "-"
                    w = want[i] if i < len(want) else "-"
                    if g != w:
                        print("  line %d: ref %r model %r" % (i, g, w))
                        break
    print("%d programs, %d disagreements" % (len(work), bad))
    for name, spent in slow:
        print("  slow: %s %ss" % (name, spent))
    shutil.rmtree(here.parent)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
