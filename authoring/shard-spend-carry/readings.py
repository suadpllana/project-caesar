#!/usr/bin/env python3
"""Every plausible wrong reading, as the files it would replace in the reference.

Two readers. `tools/readingcheck.py` imports the contract below and shrinks each reading down
to the smallest program that still separates it from the reference. Running this file directly
prints the first enumerated case that catches each reading and how much of a generated
population it moves - a reading that moves nothing is a correct variant or a patch that never
fired, and a reading no enumerated case catches is a hole in `cases.py`.

The reading directories are built by `make_readings.py`, which asserts that every patch fired.
"""
import importlib
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "shard-spend-carry"
READ = HERE / "readings"
PARTS = ("cell.py", "lay.py", "cut.py", "walk.py", "tick.py", "keep.py")
SKIP = {"wide", "deep"}

REFERENCE = str(TASK / "solution")

sys.path.insert(0, str(TASK / "tests"))
sys.path.insert(0, str(TASK / "tests" / "seal"))
import cases  # noqa: E402
import gen  # noqa: E402


def _readings():
    out = {}
    for here in sorted(READ.iterdir()):
        if not here.is_dir():
            continue
        files = {}
        for part in PARTS:
            mine = (here / part).read_text(encoding="utf-8")
            if mine != (pathlib.Path(REFERENCE) / part).read_text(encoding="utf-8"):
                files[part] = mine
        out[here.name] = files
    return out


READINGS = _readings()
NOTES = {here.name: (here / "NOTE").read_text(encoding="utf-8").strip()
         for here in sorted(READ.iterdir()) if here.is_dir()}

_ENGINES = {}


def _engine(policy):
    key = str(policy)
    if key in _ENGINES:
        return _ENGINES[key]
    room = pathlib.Path(tempfile.mkdtemp(prefix="ssc-read-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here)
    for part in PARTS:
        one = pathlib.Path(policy) / part
        if one.is_file():
            shutil.copy(one, here / "opt" / part)
    for name in list(sys.modules):
        if name in ("ops", "opt") or name.startswith("opt."):
            del sys.modules[name]
    sys.path.insert(0, str(here))
    ops = importlib.import_module("ops")
    reg = importlib.import_module("opt.reg")
    sys.path.pop(0)
    for name in list(sys.modules):
        if name in ("ops", "opt") or name.startswith("opt."):
            del sys.modules[name]
    _ENGINES[key] = (ops, reg)
    return _ENGINES[key]


def run(policy, text):
    ops, reg = _engine(policy)
    r = reg.Reg()
    for line in text.splitlines():
        t = tuple(line.split())
        if t:
            ops.ex(r, t)
    return r.out


def enumerated():
    return [(name, "\n".join(cases.ops(name))) for name in cases.ORDER]


def generated(n):
    out = []
    per = max(1, n // (len(gen.FAMILIES) - len(SKIP)))
    for fam, name, lines in gen.programs("readingcheck", per):
        if fam not in SKIP:
            out.append((name, "\n".join(lines)))
    return out[:n]


def main():
    import model
    pop = generated(280)
    want = {name: model.expect(text.splitlines()) for name, text in pop}
    hand = {name: model.expect(cases.ops(name)) for name in cases.ORDER}
    print("%-20s %-26s %s" % ("reading", "first case that catches it", "population moved"))
    bad = 0
    for name, files in sorted(READINGS.items()):
        alt = HERE / "readings" / name
        caught = None
        for case in cases.ORDER:
            if run(alt, "\n".join(cases.ops(case))) != hand[case]:
                caught = case
                break
        moved = sum(1 for pname, text in pop if run(alt, text) != want[pname])
        flag = ""
        if caught is None:
            flag = "  <-- NO ENUMERATED CASE CATCHES IT"
            bad += 1
        if moved == 0:
            flag += "  <-- MOVES NOTHING"
            bad += 1
        print("%-20s %-26s %5.1f%% of %d%s"
              % (name, caught or "-", 100.0 * moved / len(pop), len(pop), flag))
        print("    %s" % NOTES[name])
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
