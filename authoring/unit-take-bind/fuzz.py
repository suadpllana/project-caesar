"""Differential gate: the reference engine against the sealed model, over generated programs."""
import sys

import harness

sys.path.insert(0, str(harness.TASK / "tests"))
import gen  # noqa: E402
import model  # noqa: E402


def main():
    per = int(sys.argv[1]) if len(sys.argv) > 1 else 100
    seed = sys.argv[2] if len(sys.argv) > 2 else "fuzz"
    dst = harness.tree(harness.REF)
    go, drop = harness.in_proc(dst)
    progs = gen.programs(seed, per)
    bad = []
    fams = {}
    for fam, name, lines in progs:
        fams[fam] = fams.get(fam, 0) + 1
        try:
            got = go(lines)
        except Exception as exc:  # noqa: BLE001
            bad.append((name, "reference raised: %r" % (exc,)))
            continue
        want = model.expect(lines)
        if got != want:
            bad.append((name, "ref %r != model %r" % (got[:3], want[:3])))
    drop()
    print("programs: %d  families: %s" % (len(progs), sorted(fams.items())), flush=True)
    print("disagreements: %d" % len(bad), flush=True)
    for name, why in bad[:6]:
        print("  %s  %s" % (name, why), flush=True)
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
