"""Freeze the hand-case ground truth, and stage the verifier's pristine tree.

`gt.json` is written from the sealed model and cross-checked against the reference
solution before it lands, so the two independent implementations have to agree
before anything is frozen. Every file written here is pinned to LF and checked for
carriage returns afterwards: a generator that leaves CRLF in a shipped file is
caught by nothing else until the packaged archive is inspected.
"""
import json
import pathlib
import shutil
import sys

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "authoring" / "packed-doc-settlement"))
sys.path.insert(0, str(ROOT / "tasks" / "packed-doc-settlement" / "tests" / "seal"))

import harness  # noqa: E402
import cases  # noqa: E402
import model  # noqa: E402

TASK = ROOT / "tasks" / "packed-doc-settlement"
ENV = TASK / "environment" / "app_src"
PRISTINE = TASK / "tests" / "pristine"


def write(path, text):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")
    assert "\r" not in path.read_text(encoding="utf-8"), path


def stage_pristine():
    """The verifier's own copy of the tree: frozen runtime plus the shipped policy."""
    if PRISTINE.exists():
        shutil.rmtree(PRISTINE)
    (PRISTINE / "train").mkdir(parents=True)
    (PRISTINE / "recipes").mkdir(parents=True)
    write(PRISTINE / "run_train.py", (ENV / "run_train.py").read_text())
    for f in sorted((ENV / "train").glob("*.py")):
        write(PRISTINE / "train" / f.name, f.read_text())
    for f in sorted((ENV / "recipes").glob("*.txt")):
        write(PRISTINE / "recipes" / f.name, f.read_text())


def main():
    ref = harness.solution_tree()
    truth = {}
    for name in cases.ORDER:
        lines = cases.ops(name)
        exp, tight, near = model.margins(lines)
        got, err = ref.guarded(lines)
        assert err is None, (name, err)
        assert got == exp, name
        assert tight >= 1e-6 and near >= 1e-3, (name, tight, near)
        truth[name] = exp
    write(TASK / "tests" / "seal" / "gt.json", json.dumps(truth, indent=1, sort_keys=True) + "\n")
    stage_pristine()
    print("froze %d hand cases, %d lines" % (
        len(truth), sum(len(v) for v in truth.values())))
    print("pristine tree: %d files" % len(list(PRISTINE.rglob("*.*"))))
    return 0


if __name__ == "__main__":
    sys.exit(main())
