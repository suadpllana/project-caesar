"""Freeze the enumerated answers, and prove that nothing already frozen moved.

gt.json is the sealed side's fixed point: the grader checks that the model still reproduces
it, so a model that drifts cannot quietly redefine what correct means. This script is also
the additivity proof. Whenever a rule is added that is supposed to leave the existing
behaviour alone, every answer already in the file has to come back byte for byte; when one
moves, the run says which case and the change is a contract change, not a refinement.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import lab  # noqa: E402

cases, _gen, model = lab.sealed()
GT = lab.SEAL / "gt.json"


def main():
    before = {}
    if GT.is_file():
        before = json.loads(GT.read_text(encoding="utf-8"))
    now = {}
    for name in cases.ORDER:
        now[name] = model.trace("\n".join(cases.prog(name)) + "\n")
    moved = [n for n in before if n in now and before[n] != now[n]]
    gone = [n for n in before if n not in now]
    fresh = [n for n in now if n not in before]
    text = json.dumps(now, indent=1, sort_keys=True) + "\n"
    if "\r" in text:
        raise SystemExit("build_gt: carriage return in gt.json")
    GT.write_text(text, encoding="utf-8", newline="\n")
    print("froze %d cases, %d lines" % (len(now), sum(len(v) for v in now.values())))
    print("  new: %s" % (", ".join(sorted(fresh)) or "none"))
    print("  dropped: %s" % (", ".join(sorted(gone)) or "none"))
    if moved:
        print("  CHANGED, and every one is a contract change: %s" % ", ".join(sorted(moved)))
        return 1
    print("  changed: none - every answer already frozen came back byte for byte")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
