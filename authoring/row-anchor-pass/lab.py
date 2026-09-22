"""Load a pane tree (the shipped frozen files plus six pane files from anywhere) as a module.

    import lab
    run = lab.pane("solution")          # the reference
    run = lab.pane("shipped")           # the tree as it ships
    run = lab.pane(path_to_dir)         # six files from a variant or a reading
    lines = run(list_of_event_lines)

Each call builds its own copy under a temporary directory and imports it under a fresh package
name, so several panes can be loaded side by side in one process.
"""
import importlib
import itertools
import pathlib
import shutil
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
TASK = ROOT / "tasks" / "row-anchor-pass"
APP = TASK / "environment" / "app_src"
PARTS = ("geom.py", "band.py", "win.py", "hold.py", "move.py", "frame.py")
_n = itertools.count()


def pane(which):
    if which == "solution":
        src = TASK / "solution"
    elif which == "shipped":
        src = APP / "pane"
    else:
        src = pathlib.Path(which)
    room = pathlib.Path(tempfile.mkdtemp(prefix="rap-lab-"))
    name = "pane%d" % next(_n)
    pkg = room / name
    shutil.copytree(APP / "pane", pkg)
    for part in PARTS:
        if (src / part).is_file():
            shutil.copy(src / part, pkg / part)
    for f in pkg.glob("*.py"):
        text = f.read_text(encoding="utf-8")
        text = text.replace("from pane import", "from %s import" % name)
        text = text.replace("import pane.", "import %s." % name)
        f.write_text(text, encoding="utf-8", newline="\n")
    sys.path.insert(0, str(room))
    frame = importlib.import_module(name + ".frame")
    say = importlib.import_module(name + ".say")
    spec = importlib.import_module(name + ".spec")
    src_mod = importlib.import_module(name + ".src")

    def run(lines):
        cfg, decls, evs = spec.parse("\n".join(lines) + "\n")
        doc = src_mod.Doc(decls)
        out = say.Out()
        frame.play(cfg, doc, evs, out)
        return out.lines

    return run


# --- helpers for emit.py and cheat_report.py ------------------------------------------

SOL = TASK / "solution"
SRC = APP


def sealed():
    """(cases, gen, model) imported from the verifier side."""
    sys.path.insert(0, str(TASK / "tests"))
    sys.path.insert(0, str(TASK / "tests" / "seal"))
    import cases as _cases
    import gen as _gen
    import model as _model
    return _cases, _gen, _model


def tree(policy=None, files=None):
    """A runnable pane from a directory of six files, or from {filename: source}."""
    if files is not None:
        d = pathlib.Path(tempfile.mkdtemp(prefix="rap-files-"))
        for name, text in files.items():
            (d / name).write_text(text, encoding="utf-8", newline="\n")
        policy = d
    return pane(str(policy))


def run_text(here, text):
    return here([ln for ln in text.splitlines()])
