"""Freeze the enumerated answers, and prove a change did not move one.

Three engines must agree on every enumerated program before an answer is written: the
reference, the sealed model and the brute force in this directory. A rule change that was
meant to be additive has to leave every already-frozen answer byte for byte where it was, and
this script says so on every run - a contract change that moves one is reported by name and
has to be an intended contract change, not a surprise.

    python -u authoring/stale-cover-serve/build_gt.py [--write]
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import brute  # noqa: E402
import lab  # noqa: E402

GT = lab.TASK / "tests" / "seal" / "gt.json"


def main():
    write = "--write" in sys.argv
    cases = lab.cases()
    model = lab.model()
    here = lab.tree(lab.SOL)

    old = {}
    if GT.is_file():
        old = json.loads(GT.read_text(encoding="utf-8"))

    fresh = {}
    bad = 0
    for name in cases.ORDER:
        text = "\n".join(cases.prog(name)) + "\n"
        got = lab.run_text(here, text)
        want = model.trace(text)
        third = brute.trace(text)
        if got != want or got != third:
            bad += 1
            print("DISAGREE %s" % name)
            print("  ref   %r" % (got,))
            print("  model %r" % (want,))
            print("  brute %r" % (third,))
            continue
        fresh[name] = got

    moved = [n for n in old if n in fresh and old[n] != fresh[n]]
    added = [n for n in fresh if n not in old]
    dropped = [n for n in old if n not in fresh]
    print("cases %d, agreed %d, disagreed %d" % (len(cases.ORDER), len(fresh), bad))
    print("moved %d %s" % (len(moved), moved))
    print("added %d, dropped %d" % (len(added), len(dropped)))
    if bad:
        return 1
    if write:
        GT.write_text(json.dumps(fresh, indent=1, sort_keys=True) + "\n",
                      encoding="utf-8", newline="\n")
        assert "\r" not in GT.read_text(encoding="utf-8"), "gt.json picked up CRLF"
        print("wrote %s" % GT)
    else:
        print("(dry run; pass --write to freeze)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
