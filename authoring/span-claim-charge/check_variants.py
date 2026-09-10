"""Run each correct variant against the same population the verifier grades."""
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

HERE = pathlib.Path(__file__).resolve().parent
TASK = HERE.parent.parent / "tasks" / "span-claim-charge"
PARTS = ("dev.py", "hold.py", "item.py", "line.py", "tally.py")


def stage(over):
    room = pathlib.Path(tempfile.mkdtemp())
    tree = room / "app"
    shutil.copytree(TASK / "tests" / "pristine", tree,
                    ignore=shutil.ignore_patterns("__pycache__"))
    for part in PARTS:
        one = pathlib.Path(over) / part
        if one.is_file():
            shutil.copy(one, tree / "store" / part)
    return tree


def main():
    for over in sorted((HERE / "variants").iterdir()):
        if not over.is_dir():
            continue
        tree = stage(over)
        run = subprocess.run([sys.executable, str(HERE / "judge_one.py"), str(tree)],
                             capture_output=True, text=True, timeout=900)
        shutil.rmtree(tree.parent, ignore_errors=True)
        out = run.stdout.strip() or run.stderr[-200:]
        print("%-12s %s" % (over.name, out), flush=True)
        tree = stage(over)
        run = subprocess.run([sys.executable, str(HERE / "timeit.py"), "--tree", str(tree)],
                             capture_output=True, text=True, timeout=1800)
        shutil.rmtree(tree.parent, ignore_errors=True)
        print("%-12s %s" % ("", run.stdout.strip().splitlines()[-1:] or run.stderr[-200:]),
              flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
