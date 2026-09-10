"""Freeze the enumerated answers from the sealed model.

Answers already in gt.json must come back byte-identical: a rule change that moves one is a
contract change and has to be seen, not absorbed.
"""
import json, pathlib, sys
R = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(R / "tasks/aside-fit-sweep/tests"))
sys.path.insert(0, str(R / "tasks/aside-fit-sweep/tests/seal"))
import cases, model

GT = R / "tasks/aside-fit-sweep/tests/seal/gt.json"
old = json.loads(GT.read_text(encoding="utf-8")) if GT.is_file() else {}
new = {name: model.expect(cases.ops(name)) for name in cases.ORDER}

moved = [k for k in old if k in new and old[k] != new[k]]
gone = [k for k in old if k not in new]
if moved or gone:
    print("CONTRACT CHANGE: moved %s gone %s" % (moved, gone))
    if "--force" not in sys.argv:
        sys.exit(1)
GT.write_text(json.dumps(new, indent=1, sort_keys=True) + "\n", encoding="utf-8", newline="\n")
assert "\r" not in GT.read_text(encoding="utf-8")
print("frozen %d cases (%d new)" % (len(new), len(new) - len(old)))
