"""Assemble the tree the run executes.

Root builds it before any submitted code is loaded: the pristine copy, with the declared
artifacts laid over it. An artifact the agent never wrote is not an error - the shipped file
stands and the run is graded on what that produces. Bytecode caches do not survive, because
a cache holds code this grader never compiled.
"""
import argparse
import os
import shutil

ART = ("hst/vw.py", "hst/bd.py", "hst/ld.py", "hst/rt.py", "hst/od.py")


def clean(root):
    for base, dirs, files in os.walk(root):
        for d in list(dirs):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(base, d), ignore_errors=True)
                dirs.remove(d)
        for f in files:
            if f.endswith(".pyc"):
                os.remove(os.path.join(base, f))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pristine", required=True)
    ap.add_argument("--agent", required=True)
    ap.add_argument("--into", required=True)
    a = ap.parse_args()
    shutil.copytree(a.pristine, a.into)
    laid = 0
    for rel in ART:
        src = os.path.join(a.agent, rel)
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(a.into, rel))
            laid += 1
    clean(a.into)
    print("laid %d of %d declared artifacts" % (laid, len(ART)))


if __name__ == "__main__":
    main()
