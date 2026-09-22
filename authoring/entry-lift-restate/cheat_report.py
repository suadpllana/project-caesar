"""Run every cheat on the host and report which layer catches it, not just the reward.

A cheat that scores 0 for its own reasons looks exactly like a cheat the enumerated set
catches (CLAUDE.md, token-seam-emit). So for each wrong reading this asserts that the case
named for it in `readings.CATCHES` is among the enumerated programs that actually fail, and
reports how much of a generated sample the reading moves - a reading that moves almost
nothing is a reading the population is not shaped for.

The probes are container business: the privilege drop, the locked reward channel and the
uncollected file have no meaning on the host, so they are listed here and left to
`tools/docker_trial.py`.

    python cheat_report.py [sample-per-family]
"""

import json
import pathlib
import re
import subprocess
import sys
import tempfile

import lab
import readings

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "entry-lift-restate"
TESTS = TASK / "tests"
HERE = re.compile(r"cat > (\S+) <<'PYEOF'\n(.*?)\nPYEOF\n", re.S)

RUNNER = r'''
import json, pathlib, sys
tree, out_path, per = sys.argv[1], sys.argv[2], int(sys.argv[3])
sys.path.insert(0, "__TESTS__")
sys.path.insert(0, "__SEAL__")
sys.path.insert(0, tree)
import cases, gen, model
import run_conf
truth = json.loads(pathlib.Path("__GT__").read_text())
bad_hand = []
for name in cases.ORDER:
    lines = cases.prog(name)
    try:
        got = run_conf.run("\n".join(lines) + "\n")
    except Exception as exc:
        got = ["RAISED %s" % type(exc).__name__]
    if got != truth[name]:
        bad_hand.append(name)
moved = 0
total = 0
for fam, name, lines in gen.programs("cheat-sample", per):
    if fam in ("wide", "deep"):
        continue
    total += 1
    try:
        got = run_conf.run("\n".join(lines) + "\n")
    except Exception as exc:
        got = ["RAISED %s" % type(exc).__name__]
    if got != model.expect(lines):
        moved += 1
pathlib.Path(out_path).write_text(json.dumps(
    {"hand": bad_hand, "moved": moved, "total": total}))
'''


def stage(script):
    room = pathlib.Path(tempfile.mkdtemp(prefix="elr-cheat-"))
    tree = lab.build()
    for where, text in HERE.findall(script.read_text(encoding="utf-8")):
        rel = where[len("/app/"):]
        target = tree / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text + "\n", encoding="utf-8", newline="\n")
    return room, tree


def _hand_names():
    sys.path.insert(0, str(TESTS))
    import cases
    return cases.ORDER


def main(argv):
    per = int(argv[1]) if len(argv) > 1 else 8
    runner = (RUNNER.replace("__TESTS__", str(TESTS))
              .replace("__SEAL__", str(TESTS / "seal"))
              .replace("__GT__", str(TESTS / "seal" / "gt.json")))
    src = pathlib.Path(tempfile.mkdtemp(prefix="elr-run-")) / "runner.py"
    src.write_text(runner, encoding="utf-8", newline="\n")

    catches = readings.CATCHES
    rows, findings = [], []
    for script in sorted((TASK / "cheat").glob("cheat-*.sh")):
        name = script.stem[len("cheat-"):]
        if name.startswith("probe-"):
            rows.append((name, "container only", "", ""))
            continue
        room, tree = stage(script)
        out = room / "out.json"
        try:
            subprocess.run([sys.executable, str(src), str(tree), str(out), str(per)],
                           timeout=120, capture_output=True, text=True)
        except subprocess.TimeoutExpired:
            rows.append((name, "did not finish", "", "the worker clock ends it"))
            continue
        if not out.is_file():
            rows.append((name, "crashed", "", ""))
            findings.append("%s: produced no result" % name)
            continue
        got = json.loads(out.read_text())
        want = catches.get(name)
        if name in readings.SLOW:
            note = "correct; the worker clock is what stops it"
            if got["hand"] or got["moved"]:
                findings.append("%s: is meant to be exactly correct and is not" % name)
        elif want is None:
            note = ""
            if not got["hand"] and not got["moved"]:
                findings.append("%s: matches the reference everywhere sampled" % name)
        elif want in got["hand"]:
            note = "caught by %s" % want
        else:
            note = "NOT CAUGHT by %s" % want
            findings.append("%s: %s (failing: %s)"
                            % (name, note, ", ".join(got["hand"][:5]) or "nothing"))
        rows.append((name, "%d of %d hand" % (len(got["hand"]), len(_hand_names())),
                     "%d%% of %d sampled" % (round(100 * got["moved"] / max(got["total"], 1)),
                                             got["total"]),
                     note))

    width = max(len(r[0]) for r in rows)
    for row in rows:
        print("%-*s  %-16s %-18s %s" % (width, *row), flush=True)
    print()
    if findings:
        print("FINDINGS")
        for f in findings:
            print("  " + f)
        return 1
    print("every wrong reading is caught by the enumerated case named for it")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
