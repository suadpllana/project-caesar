"""The reference, the sealed model and (on the small families) the brute-force transcription,
held to each other over a generated population.

    python3 -u agree.py [seed] [per] [--no-brute] [--pane DIR]

Prints, per family, how many programs the panes disagree on and how long each took. With
--pane, the named directory of six pane files is held to the model instead of the reference.
"""
import sys
import time

import brute
import lab

sys.path.insert(0, str(lab.TASK / "tests"))
sys.path.insert(0, str(lab.TASK / "tests" / "seal"))
import gen  # noqa: E402
import model  # noqa: E402


def main(argv):
    args = [a for a in argv[1:] if not a.startswith("--")]
    seed = args[0] if args else "agree"
    per = int(args[1]) if len(args) > 1 else 30
    use_brute = "--no-brute" not in argv
    pane_dir = argv[argv.index("--pane") + 1] if "--pane" in argv else "solution"
    run = lab.pane(pane_dir)
    fams = {}
    for fam, name, lines in gen.programs(seed, per):
        t = time.time()
        want = model.expect(lines)
        tm = time.time() - t
        t = time.time()
        got = run(lines)
        tr = time.time() - t
        bad = got != want
        bb = False
        big = dict(gen.FAMILIES)[fam]
        if use_brute and not big:
            bb = brute.expect(lines) != want
        rec = fams.setdefault(fam, [0, 0, 0, 0.0, 0.0])
        rec[0] += 1
        rec[1] += bad
        rec[2] += bb
        rec[3] += tm
        rec[4] += tr
        if bad or bb:
            print("DIFF %s pane=%s brute=%s" % (name, bad, bb), flush=True)
    tot_m = tot_r = 0.0
    for fam, (n, bad, bb, tm, tr) in fams.items():
        tot_m += tm
        tot_r += tr
        print("%-6s n=%3d pane-vs-model=%d brute-vs-model=%d  model %.1fs  pane %.1fs"
              % (fam, n, bad, bb, tm, tr), flush=True)
    print("total model %.1fs pane %.1fs" % (tot_m, tot_r), flush=True)


if __name__ == "__main__":
    main(sys.argv)
