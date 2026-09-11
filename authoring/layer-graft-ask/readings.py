"""The wrong readings, and whether the enumerated set separates each of them.

The readings are read back out of `tasks/layer-graft-ask/cheat/`, not written again here, so a
reading and the cheat that stands for it cannot drift apart. The probes, the three
correct-but-over-budget families and the forgery are left out: none of them is a reading of the
contract, and the first two are separated by the limit rather than by a case.

Contract used by tools/readingcheck.py: REFERENCE, READINGS, run(policy, text), enumerated(),
generated(n).
"""
import importlib
import re
import shutil
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
TASK = ROOT / "tasks" / "layer-graft-ask"
sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(HERE))

import cases  # noqa: E402
import gen  # noqa: E402
import lab  # noqa: E402

REFERENCE = str(TASK / "solution")
PARTS = ("pile.py", "past.py", "made.py", "roll.py", "work.py", "ans.py")
BLOCK = re.compile(r"cat > /app/cfg/([a-z]+\.py) <<'PYEOF'\n(.*?)\nPYEOF\n", re.S)
SKIP = ("probe-", "slow-", "forge-")


def _readings():
    out = {}
    for script in sorted((TASK / "cheat").glob("cheat-*.sh")):
        name = script.stem[len("cheat-"):]
        if name.startswith(SKIP):
            continue
        found = dict(BLOCK.findall(script.read_text(encoding="utf-8")))
        ref = {p: (Path(REFERENCE) / p).read_text(encoding="utf-8") for p in PARTS}
        out[name] = {p: body + "\n" for p, body in found.items()
                     if body + "\n" != ref[p]}
    return out


READINGS = _readings()

_staged = {}
_live = [None]


def _tree(policy):
    key = str(policy)
    if key not in _staged:
        _staged[key] = lab.stage([Path(policy)])
    return _staged[key]


def run(policy, text):
    """One plan under one policy directory, as the shipped driver would run it."""
    work = _tree(policy)
    if _live[0] != str(work):
        for mod in [m for m in sys.modules if m == "cfg" or m.startswith("cfg.")]:
            del sys.modules[mod]
        sys.path = [str(work)] + [p for p in sys.path if not p.startswith("/tmp/lgalab-")]
        _live[0] = str(work)
    lex = importlib.import_module("cfg.lex")
    past = importlib.import_module("cfg.past")
    ans = importlib.import_module("cfg.ans")
    plan = lex.parse(text)
    hist = past.build(plan)
    return [ans.answer(hist, q) for q in plan.asks]


def enumerated():
    return [(name, cases.PLANS[name]) for name in sorted(cases.PLANS)]


def generated(n):
    per = max(1, n // len(gen.FAMS))
    return [(name, text) for name, text in gen.programs("readingcheck", per, scale=0)]


def reductions(text):
    """Drop a query first, then an entry, then a layer - and keep the plan parseable."""
    lines = text.split("\n")
    order = ([i for i, l in enumerate(lines) if l.startswith(("ask", "tot"))]
             + [i for i, l in enumerate(lines) if l.startswith(("put", "cut", "mix"))]
             + [i for i, l in enumerate(lines) if l == "lay"])
    for i in reversed(order):
        cut = lines[:i] + lines[i + 1:]
        layers = sum(1 for l in cut if l == "lay")
        ok = True
        for l in cut:
            bits = l.split(" ")
            if bits[0] in ("ask", "tot") and len(bits) == 3 and int(bits[2]) > layers:
                ok = False
                break
        if ok and any(l.startswith(("ask", "tot")) for l in cut):
            yield "\n".join(cut)


def cleanup():
    for work in _staged.values():
        shutil.rmtree(work, ignore_errors=True)
