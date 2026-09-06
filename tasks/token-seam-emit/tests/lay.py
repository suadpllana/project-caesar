"""Assemble the tree the run executes: a pristine copy with the declared artifacts laid over it.

Run by root before any submitted code is loaded. A declared artifact the agent never wrote
is not an error here - it is simply absent, the shipped file stands, and the run is graded
on what that produces.
"""
import argparse
import os
import shutil

ART = ("strm/sm.py", "strm/hb.py", "strm/rel.py", "strm/fin.py")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pristine", required=True)
    ap.add_argument("--agent", required=True)
    ap.add_argument("--into", required=True)
    a = ap.parse_args()

    shutil.copytree(a.pristine, a.into)
    for rel in ART:
        src = os.path.join(a.agent, rel)
        if os.path.isfile(src):
            shutil.copyfile(src, os.path.join(a.into, rel))

    # Bytecode caches carry code the grader never compiled, so they do not survive here.
    for root, dirs, files in os.walk(a.into):
        for d in list(dirs):
            if d == "__pycache__":
                shutil.rmtree(os.path.join(root, d), ignore_errors=True)
                dirs.remove(d)
        for f in files:
            if f.endswith(".pyc"):
                os.remove(os.path.join(root, f))


if __name__ == "__main__":
    main()
