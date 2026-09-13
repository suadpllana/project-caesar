"""Does the reference reproduce every frozen answer, and does the sealed model?

    python3 agree.py            reference against gt.json, then model against gt.json
"""
import json
import pathlib
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

TESTS = lab.TASK / "tests"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))
import cases  # noqa: E402


def main(argv):
    gt = json.loads((TESTS / "seal" / "gt.json").read_text(encoding="utf-8"))
    which = argv[0] if argv else "both"
    bad = 0
    if which in ("ref", "both"):
        lb = lab.Lab(lab.TASK / "solution")
        for name in sorted(cases.PLANS):
            got = lb.run(cases.PLANS[name])
            if name in gt and got != gt[name]:
                bad += 1
                print("REF differs on %s\n   want %s\n   got  %s" % (name, gt[name], got))
            elif name not in gt:
                print("REF new case %s -> %s" % (name, got))
        lb.close()
        print("reference: %d frozen answers checked, %d wrong" % (len(gt), bad))
    if which in ("model", "both"):
        import model
        mbad = 0
        for name in sorted(cases.PLANS):
            if name in gt and model.trace(cases.PLANS[name]) != gt[name]:
                mbad += 1
                print("MODEL differs on %s" % name)
        print("model: %d frozen answers checked, %d wrong" % (len(gt), mbad))
        bad += mbad
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
