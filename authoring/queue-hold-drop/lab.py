"""Build an overlay tree outside the bundle and run a program through it.

Nothing here writes inside tasks/queue-hold-drop: an authoring run that leaves scratch in the
bundle ships it. Everything lands in a fresh tempfile.mkdtemp.
"""
import pathlib
import shutil
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parents[2]
TASK = ROOT / "tasks" / "queue-hold-drop"
HERE = pathlib.Path(__file__).resolve().parent
PARTS = ("line.py", "fold.py", "hold.py", "view.py", "lay.py", "reach.py")


def tree(*overs):
    """A copy of the shipped tree with each `over` laid over /app/pend in turn."""
    room = pathlib.Path(tempfile.mkdtemp(prefix="qhd-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here,
                    ignore=shutil.ignore_patterns("progs", "__pycache__"))
    for over in overs:
        if over is None:
            continue
        for part in PARTS:
            one = pathlib.Path(over) / part
            if one.is_file():
                shutil.copy(one, here / "pend" / part)
    return here


def drive(here, lines):
    """Run one program inside `here`, in this process, with the tree's own modules."""
    for mod in [m for m in list(sys.modules) if m == "pend" or m.startswith("pend.")]:
        del sys.modules[mod]
    sys.path.insert(0, str(here))
    try:
        from pend import scan, step, store
        st = store.St()
        for op in scan.ops("\n".join(lines)):
            step.run(st, op)
        return list(st.out)
    finally:
        sys.path.remove(str(here))
        for mod in [m for m in list(sys.modules) if m == "pend" or m.startswith("pend.")]:
            del sys.modules[mod]


_BUILT = {}


def named(root):
    """`ref` is the shipped reference; `slow` is that reference rebuilding the view per question.

    Both are built from `solution/`, never from a second copy of it, so nothing here can drift
    from what the bundle ships.
    """
    here = _BUILT.get(root)
    if here is not None:
        return here
    if root == "ref":
        here = tree(TASK / "solution")
    elif root == "slow":
        import emit
        here = tree(TASK / "solution")
        for part, src in emit.SLOW["slow-rebuild"].items():
            (here / "pend" / part).write_text(src, encoding="utf-8", newline="\n")
    else:
        here = tree(pathlib.Path(root))
    _BUILT[root] = here
    return here


def run(lines, root="ref"):
    """Run a program through the reference, the rebuilding variant, or a directory of files."""
    return drive(named(root), lines)


def show(text, root="ref"):
    for line in run([l for l in text.strip().splitlines() if l.strip()], root):
        print(line)


if __name__ == "__main__":
    import sys as _sys
    show(pathlib.Path(_sys.argv[1]).read_text(),
         _sys.argv[2] if len(_sys.argv) > 2 else "ref")
