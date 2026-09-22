"""Differential harness: the reference through the real entry point against the sealed model."""
import importlib
import json
import shutil
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path("/home/user/project-caesar")
TASK = ROOT / "tasks" / "rekey-copy-replay"
AUTH = ROOT / "authoring" / "rekey-copy-replay"
PARTS = ("walk.py", "mark.py", "sift.py", "place.py", "wait.py", "tally.py")


def tree(which):
    room = Path(tempfile.mkdtemp(prefix="rcr-"))
    here = room / "app"
    shutil.copytree(TASK / "environment" / "app_src", here)
    if which == "ref":
        for part in PARTS:
            shutil.copy(TASK / "solution" / part, here / "reb" / part)
    elif which != "ship":
        for part in PARTS:
            src = Path(which) / part
            if src.is_file():
                shutil.copy(src, here / "reb" / part)
    return here


def loader(which):
    here = tree(which)
    sys.path.insert(0, str(here))
    for name in list(sys.modules):
        if name == "run_reb" or name.startswith("reb"):
            del sys.modules[name]
    mod = importlib.import_module("run_reb")
    return mod, here


def main():
    which = sys.argv[1] if len(sys.argv) > 1 else "ref"
    per = int(sys.argv[2]) if len(sys.argv) > 2 else 4
    only = sys.argv[3] if len(sys.argv) > 3 else None
    sys.path.insert(0, str(AUTH))
    sys.path.insert(0, str(TASK / "tests"))
    import gen
    import model_src

    mod, _here = loader(which)
    work = gen.programs("probe", per)
    if only:
        work = [w for w in work if w[0] == only]
    bad = 0
    spent = 0.0
    mspent = 0.0
    for fam, name, lines in work:
        text = "\n".join(lines) + "\n"
        t0 = time.time()
        try:
            got = mod.run(text)
        except Exception as exc:  # noqa: BLE001
            got = ["RAISED %r" % (exc,)]
        spent += time.time() - t0
        t1 = time.time()
        want = model_src.expect(lines)
        mspent += time.time() - t1
        if got != want:
            bad += 1
            if bad <= 2:
                for i in range(max(len(got), len(want))):
                    g = got[i] if i < len(got) else "<none>"
                    w = want[i] if i < len(want) else "<none>"
                    if g != w:
                        print("%s line %d: got %r want %r" % (name, i, g, w))
                        break
    print("%s: %d programs, %d disagree, engine %.1fs, model %.1fs"
          % (which, len(work), bad, spent, mspent))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
