"""Differential test: the reference, the sealed model and the brute force must agree.

Three readings of the same contract by three different methods. The brute force is far too
slow for the scale families, so it is run only on the small ones and only up to --brute
programs.

    python -u authoring/stale-cover-serve/diff.py --per 12 --brute 60
"""
import argparse
import importlib.util
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "stale-cover-serve"


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, str(path))
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def reference():
    """The shipped tree with solution/ laid over it, imported from a scratch copy."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="scs-ref-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here)
    for part in ("seg", "pick", "hole", "mend", "knit", "age", "ask"):
        shutil.copy(TASK / "solution" / ("%s.py" % part), here / "rng" / ("%s.py" % part))
    sys.path.insert(0, str(here))
    import run_rng
    return run_rng, room


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per", type=int, default=10)
    ap.add_argument("--brute", type=int, default=40)
    ap.add_argument("--seed", default="diff")
    ap.add_argument("--scale", action="store_true")
    args = ap.parse_args()

    gen = load("gen", TASK / "tests" / "gen.py")
    model = load("model", TASK / "tests" / "seal" / "model.py")
    brute = load("brute", ROOT / "authoring" / "stale-cover-serve" / "brute.py")
    run_rng, room = reference()

    work = gen.programs(args.seed, args.per)
    if not args.scale:
        work = [row for row in work if row[0] not in ("wide", "deep")]

    bad = 0
    bruted = 0
    for fam, name, lines in work:
        text = "\n".join(lines) + "\n"
        got = run_rng.run(text)
        want = model.trace(text)
        if got != want:
            bad += 1
            print("MISMATCH ref/model %s" % name)
            for i, (a, b) in enumerate(zip(got, want)):
                if a != b:
                    print("  line %d  ref %r  model %r" % (i, a, b))
                    break
            if len(got) != len(want):
                print("  lengths %d vs %d" % (len(got), len(want)))
            if bad > 3:
                break
            continue
        if bruted < args.brute and fam not in ("wide", "deep"):
            bruted += 1
            third = brute.trace(text)
            if third != want:
                bad += 1
                print("MISMATCH model/brute %s" % name)
                for i, (a, b) in enumerate(zip(want, third)):
                    if a != b:
                        print("  line %d  model %r  brute %r" % (i, a, b))
                        break
                if len(third) != len(want):
                    print("  lengths %d vs %d" % (len(want), len(third)))
                if bad > 3:
                    break

    shutil.rmtree(room, ignore_errors=True)
    print("programs %d, brute-checked %d, mismatches %d" % (len(work), bruted, bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
