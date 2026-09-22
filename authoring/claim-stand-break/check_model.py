"""The sealed model against the reference over the whole generated population."""
import sys
import time

import lab

T = lab.ROOT / "tasks" / "claim-stand-break" / "tests"
sys.path.insert(0, str(T))
sys.path.insert(0, str(T / "seal"))
import gen  # noqa: E402
import model  # noqa: E402


def main(argv):
    seed = argv[1] if len(argv) > 1 else "m1"
    per = int(argv[2]) if len(argv) > 2 else 40
    work = gen.programs(seed, per)
    room = lab.tree(lab.ROOT / "tasks" / "claim-stand-break" / "solution")
    t0 = time.time()
    ref = lab.batch(room, ["\n".join(lines) + "\n" for _f, _n, lines in work], seconds=1800)
    print("reference %.2fs over %d programs" % (time.time() - t0, len(work)))
    t0 = time.time()
    bad = []
    fam_time = {}
    for (fam, name, lines), want in zip(work, ref):
        a = time.time()
        got = model.expect(lines)
        fam_time[fam] = fam_time.get(fam, 0.0) + time.time() - a
        if got != want:
            bad.append((fam, name, want, got))
    print("model     %.2fs  (%s)" % (time.time() - t0,
          " ".join("%s %.1f" % (f, v) for f, v in sorted(fam_time.items(), key=lambda x: -x[1])[:4])))
    print("%d of %d differ" % (len(bad), len(work)))
    for fam, name, want, got in bad[:2]:
        print("== %s %s" % (fam, name))
        for j in range(max(len(got), len(want))):
            x = want[j] if j < len(want) else "<none>"
            y = got[j] if j < len(got) else "<none>"
            if x != y:
                print("   ref %-30s model %-30s" % (x, y))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
