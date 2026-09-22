"""Freeze the hand-case answers, and prove a contract change moved nothing it should not.

Every run reads the existing gt.json first and reports, case by case, which frozen answers
the current model still reproduces. A case that moves is either a contract change the author
meant or a regression; either way it is named here rather than discovered later.
"""
import json
import sys
from pathlib import Path

ROOT = Path("/home/user/project-caesar")
TESTS = ROOT / "tasks" / "rekey-copy-replay" / "tests"
GT = TESTS / "seal" / "gt.json"
sys.path.insert(0, str(TESTS))
sys.path.insert(0, str(TESTS / "seal"))

import cases  # noqa: E402
import model  # noqa: E402

old = {}
if GT.is_file():
    old = json.loads(GT.read_text(encoding="utf-8"))

fresh = {name: model.expect(cases.prog(name)) for name in cases.ORDER}

moved = [n for n in sorted(set(old) & set(fresh)) if old[n] != fresh[n]]
added = sorted(set(fresh) - set(old))
lost = sorted(set(old) - set(fresh))
print("frozen %d, held %d, moved %d, added %d, gone %d"
      % (len(fresh), len(set(old) & set(fresh)) - len(moved), len(moved), len(added), len(lost)))
for n in moved:
    print("  MOVED %s" % n)
for n in lost:
    print("  GONE  %s" % n)

text = json.dumps(fresh, indent=1, sort_keys=True) + "\n"
assert "\r" not in text, "gt.json must not carry a carriage return"
GT.write_text(text, encoding="utf-8", newline="\n")
print("wrote %s" % GT)
