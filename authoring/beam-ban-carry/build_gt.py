"""Freeze the enumerated answers, and prove that a change to the contract moved nothing else.

The file is written from the sealed model, never from the reference. On every run the answers
already on disk are compared with the ones just computed: a contract change that was meant to
be additive has to come out byte-identical on every program that was frozen before it, and a
program whose answer moved is reported by name rather than quietly rewritten.
"""
import json
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "beam-ban-carry"
SEAL = TASK / "tests" / "seal"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(SEAL))
import cases  # noqa: E402
import model  # noqa: E402

OUT = SEAL / "gt.json"


def main():
    old = {}
    if OUT.is_file():
        old = json.loads(OUT.read_text(encoding="utf-8"))
    fresh = {name: model.expect(cases.prog(name)) for name in cases.ORDER}
    moved = [name for name in sorted(set(old) & set(fresh)) if old[name] != fresh[name]]
    added = sorted(set(fresh) - set(old))
    dropped = sorted(set(old) - set(fresh))
    text = json.dumps(fresh, indent=1, sort_keys=True) + "\n"
    if "\r" in text:
        raise SystemExit("carriage return in gt.json")
    OUT.write_text(text, encoding="utf-8", newline="\n")
    print("frozen %d programs, %d new, %d gone" % (len(fresh), len(added), len(dropped)))
    if moved:
        print("CONTRACT CHANGE - these answers moved: %s" % ", ".join(moved))
    elif old:
        print("every answer already on disk came out byte-identical")


if __name__ == "__main__":
    main()
