"""Assemble a runnable tree and run a batch of programs through it, out of tree.

Every tree is built in a temp directory outside the bundle so an authoring run can never leave
a file inside tasks/claim-stand-break/ for package.py to pick up.
"""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent.parent
TASK = ROOT / "tasks" / "claim-stand-break"
SRC = TASK / "environment" / "app_src"
PARTS = ("rows", "hold", "view", "cover", "watch", "path")
FROZEN = ("run_tx.py", "tx/__init__.py", "tx/prog.py", "tx/say.py")

BATCH = '''
import json, sys
sys.path.insert(0, sys.argv[1])
import run_tx
work = json.load(open(sys.argv[2]))
out = []
for text in work:
    try:
        out.append(run_tx.run(text))
    except Exception as exc:
        out.append(["!! %s: %s" % (type(exc).__name__, exc)])
json.dump(out, open(sys.argv[3], "w"))
'''


def tree(over=None):
    """Frozen files, the shipped modules, and whatever `over` holds laid on top."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="csb-"))
    (room / "tx").mkdir()
    for name in FROZEN:
        shutil.copy(SRC / name, room / name)
    for part in PARTS:
        one = SRC / "tx" / ("%s.py" % part)
        if one.is_file():
            shutil.copy(one, room / "tx" / ("%s.py" % part))
    if over:
        for one in pathlib.Path(over).glob("*.py"):
            shutil.copy(one, room / "tx" / one.name)
    (room / "_batch.py").write_text(BATCH, encoding="utf-8")
    return room


def batch(room, texts, seconds=600):
    """Run every program through the tree in one child process and return the traces."""
    work = pathlib.Path(tempfile.mkdtemp(prefix="csb-work-"))
    src = work / "in.json"
    dst = work / "out.json"
    src.write_text(json.dumps(texts), encoding="utf-8")
    proc = subprocess.run([sys.executable, str(room / "_batch.py"), str(room), str(src), str(dst)],
                          capture_output=True, text=True, timeout=seconds)
    if proc.returncode != 0:
        raise RuntimeError("batch failed: %s%s" % (proc.stdout[-2000:], proc.stderr[-2000:]))
    got = json.loads(dst.read_text(encoding="utf-8"))
    shutil.rmtree(work, ignore_errors=True)
    return got


def run_one(room, text):
    return batch(room, [text])[0]


def engine(room):
    """Import run_tx out of a built tree, with the module cache purged first."""
    import importlib
    for name in [n for n in list(sys.modules) if n == "tx" or n.startswith("tx.")
                 or n == "run_tx"]:
        del sys.modules[name]
    sys.path.insert(0, str(room))
    try:
        return importlib.import_module("run_tx")
    finally:
        sys.path.pop(0)


def run_text(room, text):
    """One program through one built tree, in this process."""
    return engine(room).run(text if text.endswith("\n") else text + "\n")


def sealed():
    """The verifier's own case list, generator and model."""
    where = ROOT / "tasks" / "claim-stand-break" / "tests"
    for one in (where, where / "seal"):
        if str(one) not in sys.path:
            sys.path.insert(0, str(one))
    import cases
    import gen
    import model
    return cases, gen, model
