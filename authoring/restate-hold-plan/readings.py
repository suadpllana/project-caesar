"""The wrong readings, for tools/readingcheck.py and tools/tracecheck.py. Never ships.

The readings are built by emit.py - the same files the cheats in cheat/ carry - so the readings
measured here and the cheats that ship cannot drift apart. EDITS is the literal list of their
names that tracecheck reads; READINGS maps each name to the planner files it replaces.

    python tools/readingcheck.py restate-hold-plan [rounds]
"""
import pathlib
import random
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import emit  # noqa: E402
import lab  # noqa: E402

EDITS = [
    "pins-expire", "keep-inclusive", "keep-from-start", "reach-existing-only",
    "reach-window-back", "reach-prev-same-day", "stand-any", "stand-all-missing", "stand-never",
    "stand-runs-only", "no-temp", "run-if-reached", "same-before-lost", "sub-over-part",
    "sub-through-temps", "temp-always-changed", "same-agrees", "pinned-agrees", "closure", "temps-of-holds",
    "temp-per-reader", "order-static", "order-fix-after-sort", "holds-interleaved",
]

REFERENCE = str(lab.SOL)

emit.OUT.mkdir(exist_ok=True)
for _build in emit.READING_BUILDERS:
    _build()
READINGS = dict(emit.READINGS)
assert sorted(READINGS) == sorted(EDITS), sorted(set(READINGS) ^ set(EDITS))

cases, gen, _model = lab.sealed()
_TREES = {}


def run(policy, text):
    """Plan one pipeline with one directory of the five planner files."""
    here = _TREES.get(str(policy))
    if here is None:
        here = _TREES[str(policy)] = lab.tree(policy)
    return lab.run_text(here, text if text.endswith("\n") else text + "\n")


def enumerated():
    return [(name, "\n".join(cases.prog(name)) + "\n") for name in cases.ORDER]


def generated(n):
    out = []
    small = [fam for fam, big in gen.FAMILIES if not big]
    per = max(1, n // len(small))
    for fam in small:
        for k in range(per):
            rng = random.Random("reading|%s|%d" % (fam, k))
            out.append(("%s-%d" % (fam, k), "\n".join(gen.build(fam, rng)) + "\n"))
    return out


def reductions(text):
    """Smaller pipelines: drop a pin, a stand-in, or a step nothing else reads."""
    lines = text.strip("\n").split("\n")
    for k, line in enumerate(lines):
        if line.split()[0] in ("pin", "stand"):
            yield "\n".join(lines[:k] + lines[k + 1:]) + "\n"
    for k, line in enumerate(lines):
        ws = line.split()
        if ws[0] != "step":
            continue
        name = ws[1]
        used = any(name in (tok.split("/")[0].split("~")[0].rsplit("-1", 1)[0])
                   for other in lines if other.split()[0] == "step" and other != line
                   for tok in other.split()[4:])
        named = any(other.split()[0] in ("pin", "stand") and name in other.split()[1:3]
                    for other in lines)
        if not used and not named:
            yield "\n".join(lines[:k] + lines[k + 1:]) + "\n"
