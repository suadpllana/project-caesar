"""Every correct implementation must print what the sealed model prints, journal for journal.

    python3 authoring/journal-gap-mend/agree.py <seed> <per> [dir ...]

Checks the reference (solution/) and every directory under variants/ by default, on the
generator's families at `per` journals each, and reports time per family.
"""
import pathlib
import sys
import time

sys.dont_write_bytecode = True  # never leave __pycache__ inside the bundle

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import readings  # noqa: E402

readings._sealed()
import gen  # noqa: E402
import model  # noqa: E402


def main(argv):
    seed, per = argv[0], int(argv[1])
    dirs = argv[2:] or [readings.REFERENCE] + sorted(str(p) for p in (HERE / "variants").iterdir()
                                                     if p.is_dir())
    progs = gen.programs(seed, per)
    want = {name: tuple(model.expect(text)) for _f, name, text in progs}
    worst = 0
    for d in dirs:
        bad = []
        fam_t = {}
        for fam, name, text in progs:
            t0 = time.time()
            got = readings.run(d, text)
            fam_t[fam] = fam_t.get(fam, 0.0) + time.time() - t0
            if got != want[name]:
                bad.append(name)
        total = sum(fam_t.values())
        print("%-60s %d/%d agree  %.1fs  (busy %.1fs)" % (
            d.replace(str(HERE.parent.parent) + "/", ""), len(progs) - len(bad), len(progs),
            total, fam_t.get("busy", 0.0)), flush=True)
        if bad:
            worst = 1
            print("   first disagreements:", bad[:5], flush=True)
    return worst


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
