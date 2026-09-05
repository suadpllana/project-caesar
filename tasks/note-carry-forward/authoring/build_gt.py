"""Write tests/gt.json, and refuse to write one that cannot be proved.

The truth for the hand-written streams comes from the sealed model in
tests/oracle.py, which shares no code with the environment or the reference.
It is only written out once the reference, run through the real board, agrees
with it on every one of them and on a block of generated streams as well.
"""
import json
import pathlib
import sys

TASK = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "environment" / "app_src"))

import oracle  # noqa: E402
import scen  # noqa: E402


def reference_board(revs, events):
    """The reference, driven exactly as the runner drives a submission."""
    import importlib
    import types
    holder = types.ModuleType("refhold")
    src = (TASK / "solution" / "board.py").read_text()
    rulesrc = (TASK / "solution" / "rule.py").read_text()
    rule = types.ModuleType("note.rule")
    exec(compile(rulesrc, "rule.py", "exec"), rule.__dict__)
    sys.modules["note.rule"] = rule
    import note
    note.rule = rule
    exec(compile(src, "board.py", "exec"), holder.__dict__)
    from rev.store import Store
    store = Store()
    for lines in revs:
        store.land(lines)
    threads, log = holder.Board(store).build([tuple(e) for e in events])
    table = sorted([[int(t["id"]), str(t["state"]),
                     sorted(int(x) for x in t["span"])] for t in threads])
    return {"threads": table,
            "log": [[str(e[0])] + [int(x) for x in e[1:]] for e in log]}


def main():
    fixed = {}
    for item in scen.FIXED:
        threads, log = oracle.board(item["revs"], item["events"])
        want = {"threads": threads, "log": log}
        got = reference_board(item["revs"], item["events"])
        if got != want:
            raise SystemExit("reference and sealed model differ on %s\n  model %s\n  ref   %s"
                             % (item["name"], want, got))
        fixed[item["name"]] = want

    checked = 0
    for seed in (1, 2, 3):
        for item in scen.generated(120, seed):
            threads, log = oracle.board(item["revs"], item["events"])
            if reference_board(item["revs"], item["events"]) != {"threads": threads, "log": log}:
                raise SystemExit("reference and sealed model differ on %s (seed %d)"
                                 % (item["name"], seed))
            checked += 1

    wide = 0
    for seed in (1, 2):
        for item in scen.wide(3, seed):
            threads, log = oracle.board(item["revs"], item["events"])
            if reference_board(item["revs"], item["events"]) != {"threads": threads, "log": log}:
                raise SystemExit("reference and sealed model differ on %s (seed %d)"
                                 % (item["name"], seed))
            wide += 1

    out = TASK / "tests" / "gt.json"
    with open(out, "w", newline="\n") as fh:
        json.dump({"fixed": fixed}, fh, indent=1, sort_keys=True)
        fh.write("\n")
    print("gt.json written: %d hand-written, %d generated and %d wide streams agreed"
          % (len(fixed), checked, wide))


if __name__ == "__main__":
    main()
