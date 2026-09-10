"""Freeze the answers to the enumerated programs, from the sealed model.

The file is additive on purpose: an answer that is already frozen must come out byte-identical
after any later change, and a change that moves one is a contract change and is reported as
such rather than quietly written. Run it after every edit to cases.py or to the model.
"""
import json
import pathlib
import sys

TASK = pathlib.Path(__file__).resolve().parents[2] / "tasks" / "slab-fold-scope"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
import cases  # noqa: E402
import model  # noqa: E402

GT = TASK / "tests" / "seal" / "gt.json"


def main():
    was = {}
    if GT.is_file():
        was = json.loads(GT.read_text(encoding="utf-8"))
    now = {name: model.expect(cases.ops(name)) for name in cases.ORDER}
    moved = [n for n in sorted(set(was) & set(now)) if was[n] != now[n]]
    added = sorted(set(now) - set(was))
    dropped = sorted(set(was) - set(now))
    allowed = set()
    for arg in sys.argv:
        if arg.startswith("--moved="):
            allowed = set(arg.split("=", 1)[1].split(","))
    moved = [n for n in moved if n not in allowed]
    if moved and "--contract" not in sys.argv:
        for name in moved:
            print("MOVED %s" % name)
            for a, b in zip(was[name], now[name]):
                if a != b:
                    print("   was %-30s now %s" % (a, b))
        raise SystemExit(
            "%d frozen answers moved; re-run with --contract only if the contract really "
            "changed" % len(moved))
    text = json.dumps(now, indent=1, sort_keys=True) + "\n"
    assert "\r" not in text
    GT.write_text(text, encoding="utf-8", newline="\n")
    print("frozen %d programs, %d added, %d dropped, %d moved"
          % (len(now), len(added), len(dropped), len(moved)))


if __name__ == "__main__":
    main()
