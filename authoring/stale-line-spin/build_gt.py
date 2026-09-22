"""Freeze the hand cases' expected lines into tests/seal/gt.json.

Additivity check: when gt.json already exists, every entry it holds must come out of the model
byte-for-byte unchanged, so a model edit that silently redefines correct for a frozen case is
refused. A deliberate contract change is made by deleting the entry, never by overwriting it.
Written with newline="\\n" and checked for carriage returns (CLAUDE.md, reach-pair-sweep).
"""
import json
import os
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
TESTS = os.path.join(ROOT, "tasks", "stale-line-spin", "tests")
sys.path.insert(0, os.path.join(TESTS, "seal"))
sys.path.insert(0, TESTS)

import cases  # noqa: E402
import model  # noqa: E402

GT = os.path.join(TESTS, "seal", "gt.json")

old = {}
if os.path.isfile(GT):
    with open(GT, encoding="utf-8") as f:
        old = json.load(f)

new = {name: model.expect(cases.prog(name)) for name in cases.ORDER}
moved = [n for n in old if n in new and old[n] != new[n]]
if moved:
    sys.exit("refusing: frozen answers would change for %s" % moved)
gone = [n for n in old if n not in new]
text = json.dumps(new, indent=1, sort_keys=True) + "\n"
assert "\r" not in text
with open(GT, "w", encoding="utf-8", newline="\n") as f:
    f.write(text)
print("gt.json: %d cases (%d already frozen, %d new, %d removed)" % (
    len(new), len(old) - len(gone), len(new) - (len(old) - len(gone)), len(gone)))
