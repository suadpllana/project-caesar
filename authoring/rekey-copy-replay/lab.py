"""Shared bench for the authoring scripts: build a tree under one set of six files and run a
program through the real entry point. Everything is written under tempfile.mkdtemp, outside
the bundle, so an authoring run in flight can never be packaged."""
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "rekey-copy-replay"
SRC = TASK / "environment" / "app_src"
SOL = TASK / "solution"
PARTS = ("walk.py", "mark.py", "sift.py", "place.py", "wait.py", "tally.py")


def tree(policy=None, files=None):
    """A pristine tree with a directory of six files, or a {name: source} map, laid over it."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="rcr-lab-"))
    here = room / "app"
    shutil.copytree(SRC, here, ignore=shutil.ignore_patterns("progs", "__pycache__"))
    if policy is not None:
        for name in PARTS:
            one = pathlib.Path(policy) / name
            if one.is_file():
                shutil.copy(one, here / "reb" / name)
    if files is not None:
        lay(here, files)
    return here


def sealed():
    """The verifier's own case list, generator and model."""
    import importlib
    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "tests" / "seal"))
    return (importlib.import_module("cases"), importlib.import_module("gen"),
            importlib.import_module("model"))


def lay(here, files):
    """Write a {filename: source} mapping into an existing tree."""
    for name, src in files.items():
        (pathlib.Path(here) / "reb" / name).write_text(src, encoding="utf-8", newline="\n")


def run(here, prog, timeout=300):
    got = subprocess.run([sys.executable, "run_reb.py", str(prog)], cwd=str(here),
                         capture_output=True, text=True, timeout=timeout)
    if got.returncode != 0:
        raise RuntimeError(got.stderr.strip().splitlines()[-1:] or ["no stderr"])
    return got.stdout.splitlines()


def run_text(here, text, timeout=300):
    room = pathlib.Path(tempfile.mkdtemp(prefix="rcr-prog-"))
    prog = room / "p.txt"
    prog.write_text(text.rstrip("\n") + "\n", encoding="utf-8", newline="\n")
    try:
        return run(here, prog, timeout=timeout)
    finally:
        shutil.rmtree(room, ignore_errors=True)
