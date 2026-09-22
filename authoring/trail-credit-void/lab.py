"""Host-side bench: assemble a runnable tree from one directory of the seven files.

Everything here writes under tempfile.mkdtemp, never inside the bundle: an authoring run that
leaves scratch in the task folder ships it (CLAUDE.md, 2026-09-06, 455 zip entries instead of
70).
"""
import importlib.util
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "trail-credit-void"
SOL = TASK / "solution"
PRISTINE = TASK / "tests" / "pristine"
PARTS = ("store.py", "pred.py", "obs.py", "book.py", "void.py", "ep.py", "tally.py")


def tree(policy):
    """A fresh copy of the shipped tree with `policy`'s seven files laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="tcv-"))
    here = room / "app"
    shutil.copytree(PRISTINE, here)
    for part in PARTS:
        one = pathlib.Path(policy) / part
        if one.is_file():
            shutil.copyfile(one, here / "crd" / part)
    return here


RUN = (
    "import sys, json\n"
    "sys.path.insert(0, %r)\n"
    "import run_crd\n"
    "print(json.dumps(run_crd.run(open(%r, encoding='utf-8').read())))\n"
)


def run_text(here, text):
    """Drive one trail inside an assembled tree, in its own process."""
    import json

    room = pathlib.Path(here).parent
    trail = room / "__in.txt"
    trail.write_text(text if text.endswith("\n") else text + "\n",
                     encoding="utf-8", newline="\n")
    done = subprocess.run([sys.executable, "-c", RUN % (str(here), str(trail))],
                          capture_output=True, text=True)
    if done.returncode != 0:
        return ("raised", tuple(done.stderr.strip().splitlines()[-1:]))
    return tuple(json.loads(done.stdout))


def sealed():
    """cases, gen and the sealed model, imported from the verifier's own directory."""
    tests = TASK / "tests"
    sys.path.insert(0, str(tests))
    sys.path.insert(0, str(tests / "seal"))
    import cases
    import gen

    spot = importlib.util.spec_from_file_location("model", tests / "seal" / "model.py")
    model = importlib.util.module_from_spec(spot)
    spot.loader.exec_module(model)
    return cases, gen, model
